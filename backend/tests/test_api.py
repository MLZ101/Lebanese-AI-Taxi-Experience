"""Phase 3: the full turn cycle, including everything that can go wrong."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app import config, engine, service
from app.ai.base import AIError
from app.main import app
from app.models import AISuggestion, Verdict
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
        self.verdicts = 0

    async def suggest(self, state):
        self.calls += 1
        if self.error:
            raise self.error
        return AISuggestion.model_validate(
            {"question": self.question, "thinking": "hmmm", **self.extra}
        )

    async def verdict(self, state):
        if self.error:
            raise self.error
        self.verdicts += 1
        return Verdict.model_validate(
            {"money_verdict": "Ma3o masari", "background_verdict": "Min el day3a",
             "guess": "Enta masi7i, sa7?", "if_right": "Shoft?", "if_wrong": "La2 la2",
             "evidence": ["el sayyara"], "fare": "20 alf", "closing_line": "Rou7 bi salemeh"}
        )


@pytest.fixture
def stub(monkeypatch):
    provider = StubProvider()
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
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
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
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
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
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
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
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
    monkeypatch.setattr(service, "get_provider", lambda *_: StubProvider(error=error))
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
    monkeypatch.setattr(service, "get_provider", lambda *_: StubProvider(error=AIError("down")))
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


# --- model selection -------------------------------------------------------- #


def test_models_endpoint_lists_the_catalog(client):
    body = client.get("/ai/models").json()
    ids = [m["id"] for m in body["models"]]
    assert "fallback" in ids
    assert all({"id", "label", "provider", "available"} <= set(m) for m in body["models"])


def test_start_records_the_chosen_model(client):
    body = client.post("/game/start", json={"model": "fallback"}).json()
    assert body["model"] == "fallback"


def test_unknown_model_falls_back_instead_of_failing(client):
    body = client.post("/game/start", json={"model": "no-such-model"})
    assert body.status_code == 200
    assert body.json()["model"]  # resolved to something usable


def test_the_chosen_model_drives_the_whole_ride(client):
    """A session keeps its brain - it must not drift to the global default."""
    session = client.post("/game/start", json={"model": "fallback"}).json()
    body = client.post(
        "/game/answer", json={"session_id": session["session_id"], "answer": "Hamra"}
    ).json()
    assert body["model"] == "fallback"
    assert body["ai_degraded"] is False  # the scripted driver is a real choice


# --- the reveal ------------------------------------------------------------- #


def test_no_verdict_while_the_ride_is_running(client, stub):
    start = client.post("/game/start").json()
    assert start["verdict"] is None
    body = client.post(
        "/game/answer", json={"session_id": start["session_id"], "answer": "Hamra"}
    ).json()
    assert body["game_status"] == "active"
    assert body["verdict"] is None


def test_the_reveal_arrives_with_the_ending(client, monkeypatch):
    provider = StubProvider(religion_confidence_change=10)
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
    session = client.post("/game/start").json()["session_id"]
    for _ in range(engine.MAX_MESSAGES):
        body = client.post(
            "/game/answer", json={"session_id": session, "answer": "eh"}
        ).json()
        if body["game_status"] == "ended":
            break
    assert body["game_status"] == "ended"
    assert body["verdict"]["money_verdict"]
    assert body["verdict"]["background_verdict"]
    assert provider.verdicts == 1  # asked for exactly once


def test_early_reveal_fires_well_before_the_message_limit(client, monkeypatch):
    """Ninety on the background theory and he stops asking, however early."""
    provider = StubProvider(religion_confidence_change=10)
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
    session = client.post("/game/start").json()["session_id"]
    for _ in range(engine.MAX_MESSAGES):
        body = client.post(
            "/game/answer", json={"session_id": session, "answer": "min Zahle"}
        ).json()
        if body["game_status"] == "ended":
            break
    assert body["end_reason"] == engine.END_BY_EARLY_REVEAL
    assert body["message_count"] == 9  # 0 -> 90 at +10 a turn
    assert body["message_count"] < engine.MAX_MESSAGES
    assert body["verdict"]


def test_a_failed_verdict_still_produces_a_reveal(client, monkeypatch):
    """Losing the payoff is the one failure the player would actually notice."""
    monkeypatch.setattr(
        service, "get_provider", lambda *_: StubProvider(error=AIError("down"))
    )
    session = client.post("/game/start").json()["session_id"]
    for _ in range(engine.MAX_MESSAGES):
        body = client.post(
            "/game/answer", json={"session_id": session, "answer": "eh"}
        ).json()
        if body["game_status"] == "ended":
            break
    assert body["game_status"] == "ended"
    assert body["verdict"]["background_verdict"]  # the scripted one stood in
    assert body["ai_degraded"] is True


def test_the_reveal_carries_a_named_guess_and_both_reactions(client, monkeypatch):
    """The guess is the payoff - it must survive all the way to the client."""
    provider = StubProvider(religion_confidence_change=10)
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
    session = client.post("/game/start").json()["session_id"]
    for _ in range(engine.MAX_MESSAGES):
        body = client.post(
            "/game/answer", json={"session_id": session, "answer": "min Zahle"}
        ).json()
        if body["game_status"] == "ended":
            break
    verdict = body["verdict"]
    assert verdict["guess"]
    assert verdict["if_right"]
    assert verdict["if_wrong"]


def test_a_blank_guess_is_backfilled(client, monkeypatch):
    """An empty headline would be a hole exactly where the joke goes."""

    class BlankGuess(StubProvider):
        async def verdict(self, state):
            return Verdict.model_validate(
                {"money_verdict": "x", "background_verdict": "y", "guess": ""}
            )

    provider = BlankGuess(religion_confidence_change=10)
    monkeypatch.setattr(service, "get_provider", lambda *_: provider)
    session = client.post("/game/start").json()["session_id"]
    for _ in range(engine.MAX_MESSAGES):
        body = client.post(
            "/game/answer", json={"session_id": session, "answer": "min Zahle"}
        ).json()
        if body["game_status"] == "ended":
            break
    assert body["verdict"]["guess"]  # backfilled, not blank
    assert body["verdict"]["if_right"]
    assert body["ai_degraded"] is False  # the turn itself was fine
