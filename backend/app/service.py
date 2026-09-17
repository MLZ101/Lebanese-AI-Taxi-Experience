"""Turn orchestration: the layer between FastAPI and the pure engine rules.

One full turn is:
    record answer -> ask the AI -> validate -> engine applies -> engine decides
Every step after "ask the AI" is ours. A provider failure degrades to the
scripted driver; it never reaches the player as an error.
"""

from __future__ import annotations

import logging

from . import engine
from .ai import canned_suggestion, get_provider
from .models import GameState
from .sessions import SessionStore

log = logging.getLogger(__name__)

MAX_ANSWER_LENGTH = 500


class GameError(Exception):
    """Base for problems the API turns into a clean HTTP status."""


class SessionNotFound(GameError):
    pass


class GameAlreadyEnded(GameError):
    pass


class InvalidAnswer(GameError):
    pass


def start_game(store: SessionStore) -> GameState:
    """Open a ride with Abu Fadi's opening question already waiting."""
    return store.add(engine.new_game())


def _clean_answer(answer: str) -> str:
    text = (answer or "").strip()
    if not text:
        raise InvalidAnswer("answer must not be empty")
    return text[:MAX_ANSWER_LENGTH]


async def submit_answer(
    store: SessionStore, session_id: str, answer: str
) -> tuple[GameState, bool]:
    """Play one turn. Returns the updated state and whether the AI degraded."""
    state = store.get(session_id)
    if state is None:
        raise SessionNotFound(f"no ride with id {session_id!r}")
    if state.game_status == "ended":
        raise GameAlreadyEnded("this ride is already over")

    engine.record_answer(state, _clean_answer(answer))

    degraded = False
    try:
        suggestion = await get_provider().suggest(state)
    except Exception as exc:  # noqa: BLE001 - nothing may stop the ride
        log.warning("AI turn failed for %s, using fallback: %s", session_id, exc)
        suggestion = canned_suggestion(state)
        degraded = True

    engine.apply_suggestion(state, suggestion)
    return state, degraded
