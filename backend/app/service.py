"""Turn orchestration: the layer between FastAPI and the pure engine rules.

One full turn is:
    record answer -> ask the AI -> validate -> engine applies -> engine decides
Every step after "ask the AI" is ours. A provider failure degrades to the
scripted driver; it never reaches the player as an error.
"""

from __future__ import annotations

import logging

from . import engine
from .ai import canned_suggestion, canned_verdict, get_provider, resolve
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


def start_game(store: SessionStore, model_id: str | None = None) -> GameState:
    """Open a ride. An unknown or keyless model quietly falls back to a usable one."""
    return store.add(engine.new_game(model_id=resolve(model_id)))


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
        suggestion = await get_provider(state.model_id).suggest(state)
    except Exception as exc:  # noqa: BLE001 - nothing may stop the ride
        log.warning("AI turn failed for %s, using fallback: %s", session_id, exc)
        suggestion = canned_suggestion(state)
        degraded = True

    engine.apply_suggestion(state, suggestion)

    if state.game_status == "ended":
        degraded = await _attach_verdict(state) or degraded
    return state, degraded


async def _attach_verdict(state: GameState) -> bool:
    """Ask Abu Fadi for his conclusion. Returns True if we had to fake it.

    A failed verdict must never cost the player the ending - that is the whole
    payoff - so this falls back the same way a turn does.
    """
    try:
        verdict = await get_provider(state.model_id).verdict(state)
    except Exception as exc:  # noqa: BLE001 - the reveal always happens
        log.warning("verdict failed for %s, using fallback: %s", state.session_id, exc)
        state.verdict = canned_verdict(state)
        return True

    # The guess is the entire payoff. The model occasionally returns it blank,
    # which would leave the player staring at an empty headline, so patch in
    # the scripted line rather than ship a hole where the joke goes.
    spare = canned_verdict(state)
    if not verdict.guess:
        log.warning("empty guess for %s, using the scripted one", state.session_id)
        verdict.guess = spare.guess
        verdict.if_right = verdict.if_right or spare.if_right
        verdict.if_wrong = verdict.if_wrong or spare.if_wrong
    state.verdict = verdict
    return False
