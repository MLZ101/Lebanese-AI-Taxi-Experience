"""Phase 3: the full turn cycle, including everything that can go wrong."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import config, engine, service
from app.ai.base import AIError
from app.main import app
from app.models import AISuggestion
from app.sessions import SessionStore, store


@pytest.fixture(autouse=True)
def _clean_store():
    store._sessions.clear()
    yield
    store._sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


class StubProvider:
    """Stands in for Gemini: canned answers, or an explosion on demand."""

    name = "stub"

    def __init__(self, question="W enta min wein?", error=None, **extra):
        self.question, self.error, self.extra = question, error, extra
        self.calls = 0

    async def suggest(self, state):
        self.calls += 1
        if self.error:
            raise self.error
        return AISuggestion.model_validate(
            {"question": self.question, "thinking": "hmmm", **self.extra}
        )


@pytest.fixture
def stub(monkeypatch):
    provider = StubProvider()
    monkeypatch.setattr(service, "get_provider", lambda: provider)
    return provider


# --- happy path ------------------------------------------------------------- #


def test_start_returns_opening_question_and_neutral_radar(client):
    body = client.post("/game/start").json()
    assert body["message_count"] == 0
    assert body["game_status"] == "active"
    assert body["question"]
    assert set(body["radar"]) == {"money", "status", "suspicion", "tip"}
    assert body["history"] == [{"role": "abu_fadi", "text": body["question"]}]


def test_confidence_scores_are_never_top_level(client, stub):
    """Even in debug builds they stay boxed in `debug`, never on the state."""
    start = client.post("/game/start").json()
    body = client.post(
        "/game/answer",
        json={"session_id": start["session_id"], "answer": "Hamra"},
    ).json()
    assert "money_confidence" not in body
    assert "religion_confidence" not in body


def test_debug_block_exposes_the_theory_while_enabled(client, monkeypatch):
    monkeypatch.setattr(config, "EXPOSE_DEBUG", True)
    provider = StubProvider(money_confidence_change=9, religion_confidence_change=4)
    monkeypatch.setattr(service, "get_provider", lambda: provider)
    session = client.post("/game/start").json()["session_id"]
    body = client.post(
        "/game/answer", json={"session_id": session, "answer": "Mercedes"}
    ).json()
    assert body["debug"]["money_confidence"] == 9
    assert body["debug"]["religion_confidence"] == 4
    assert body["debug"]["confidence_threshold"] == engine.CONFIDENCE_END_THRESHOLD


def test_debug_block_vanishes_when_disabled(client, stub, monkeypatch):
    """Flipping the flag is all it takes to ship the game without spoilers."""
    monkeypatch.setattr(config, "EXPOSE_DEBUG", False)
    session = client.post("/game/start").json()["session_id"]
    body = client.post(
        "/game/answer", json={"session_id": session, "answer": "Hamra"}
    ).json()
    assert body["debug"] is None


def test_answer_advances_the_ride(client, stub):
    start = client.post("/game/start").json()
    response = client.post(
        "/game/answer",
        json={"session_id": start["session_id"], "answer": "Ana min Saida"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message_count"] == 1
    assert body["question"] == "W enta min wein?"
    assert body["ai_degraded"] is False
    assert [t["role"] for t in body["history"]] == ["abu_fadi", "passenger", "abu_fadi"]
    assert stub.calls == 1


def test_radar_moves_by_the_suggested_delta(client, monkeypatch):
    provider = StubProvider(radar_changes={"money": 8, "status": 0, "suspicion": 0, "tip": 0})
    monkeypatch.setattr(service, "get_provider", lambda: provider)
    start = client.post("/game/start").json()
    body = client.post(
        "/game/answer", json={"session_id": start["session_id"], "answer": "Mercedes"}
    ).json()
    assert body["radar"]["money"] == start["radar"]["money"] + 8


def test_sessions_are_independent(client, stub):
    a = client.post("/game/start").json()["session_id"]
    b = client.post("/game/start").json()["session_id"]
    client.post("/game/answer", json={"session_id": a, "answer": "one"})
    assert client.post("/game/answer", json={"session_id": b, "answer": "two"}).json()[
        "message_count"
    ] == 1


# --- error handling --------------------------------------------------------- #


def test_unknown_session_is_404(client, stub):
    response = client.post("/game/answer", json={"session_id": "nope", "answer": "hi"})
    assert response.status_code == 404


def test_answering_a_finished_ride_is_409(client, monkeypatch):
    provider = StubProvider(money_confidence_change=10, religion_confidence_change=10)
    monkeypatch.setattr(service, "get_provider", lambda: provider)
    session = client.post("/game/start").json()["session_id"]
    for _ in range(10):
        response = client.post(
            "/game/answer", json={"session_id": session, "answer": "eh"}
        )
        if response.json().get("game_status") == "ended":
            break
    assert response.json()["game_status"] == "ended"
    assert client.post(
        "/game/answer", json={"session_id": session, "answer": "more"}
    ).status_code == 409


@pytest.mark.parametrize("answer", ["", "   "])
def test_blank_answers_are_rejected(client, stub, answer):
    session = client.post("/game/start").json()["session_id"]
    response = client.post("/game/answer", json={"session_id": session, "answer": answer})
    assert response.status_code == 422


def test_overlong_answers_are_rejected(client, stub):
    session = client.post("/game/start").json()["session_id"]
    response = client.post(
        "/game/answer", json={"session_id": session, "answer": "x" * 5000}
    )
    assert response.status_code == 422


# --- AI failures must never reach the player -------------------------------- #


@pytest.mark.parametrize(
    "error",
    [AIError("bad json"), TimeoutError("timed out"), RuntimeError("boom")],
)
def test_provider_failure_degrades_to_the_scripted_driver(client, monkeypatch, error):
    monkeypatch.setattr(service, "get_provider", lambda: StubProvider(error=error))
    session = client.post("/game/start").json()["session_id"]
    response = client.post(
        "/game/answer", json={"session_id": session, "answer": "Hamra"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ai_degraded"] is True
    assert body["question"]
    assert body["message_count"] == 1


def test_a_whole_ride_survives_a_dead_provider(client, monkeypatch):
    monkeypatch.setattr(service, "get_provider", lambda: StubProvider(error=AIError("down")))
    session = client.post("/game/start").json()["session_id"]
    for _ in range(12):
        response = client.post(
            "/game/answer", json={"session_id": session, "answer": "eh w ba3den"}
        )
        if response.status_code == 409:
            break
        assert response.status_code == 200
    assert response.status_code == 409  # the ride ended on its own, it did not hang


# --- session store ---------------------------------------------------------- #


def test_store_evicts_oldest_beyond_the_cap():
    small = SessionStore(max_sessions=2)
    for _ in range(3):
        service.start_game(small)
    assert len(small) == 2


def test_health_reports_the_provider(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "model" in body
