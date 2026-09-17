"""The game engine. It owns every number in the game.

The LLM only ever hands us an `AISuggestion`. Nothing in that suggestion
reaches the player until this module has applied, clamped and rule-checked it.
"""

from __future__ import annotations

import uuid

from .models import (
    AISuggestion,
    GameState,
    Presentation,
    Radar,
    SCORE_MAX,
    SCORE_MIN,
    Turn,
    clamp,
)

# --------------------------------------------------------------------------- #
# Rules. Tuning the ride happens here and nowhere else.
# --------------------------------------------------------------------------- #

#: Abu Fadi is "sure" once both theories pass this.
CONFIDENCE_END_THRESHOLD = 70

#: From this many passenger answers on, the AI is allowed to wrap things up.
SOFT_END_MESSAGES = 7

#: Absolute ceiling. The ride ends here no matter what the AI wants.
MAX_MESSAGES = 10

#: Abu Fadi's opening line. Deliberately an ordinary taxi question - the
#: guessing game should only become visible later.
OPENING_QUESTION = "Ahla w sahla! Wein badak rou7, ya zalameh?"
OPENING_THINKING = "Another passenger..."

END_BY_CONFIDENCE = "confidence"
END_BY_MAX_MESSAGES = "max_messages"
END_BY_AI = "ai_requested"


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def new_game(session_id: str | None = None) -> GameState:
    """Start a fresh ride with Abu Fadi's opening question already on screen."""
    state = GameState(
        session_id=session_id or new_session_id(),
        radar=Radar(),
        current=Presentation(
            question=OPENING_QUESTION,
            thinking=OPENING_THINKING,
            mood="curious",
            driver_action="mirror",
        ),
    )
    state.conversation_history.append(Turn(role="abu_fadi", text=OPENING_QUESTION))
    return state


def record_answer(state: GameState, answer: str) -> None:
    """Append the passenger's reply to the transcript."""
    state.conversation_history.append(Turn(role="passenger", text=answer.strip()))


def _apply_scores(state: GameState, suggestion: AISuggestion) -> None:
    """Add the suggested deltas, then clamp every total back into 0-100."""
    changes = suggestion.radar_changes
    radar = state.radar
    radar.money = clamp(radar.money + changes.money, SCORE_MIN, SCORE_MAX)
    radar.status = clamp(radar.status + changes.status, SCORE_MIN, SCORE_MAX)
    radar.suspicion = clamp(radar.suspicion + changes.suspicion, SCORE_MIN, SCORE_MAX)
    radar.tip = clamp(radar.tip + changes.tip, SCORE_MIN, SCORE_MAX)

    state.money_confidence = clamp(
        state.money_confidence + suggestion.money_confidence_change,
        SCORE_MIN,
        SCORE_MAX,
    )
    state.religion_confidence = clamp(
        state.religion_confidence + suggestion.religion_confidence_change,
        SCORE_MIN,
        SCORE_MAX,
    )


def evaluate_ending(state: GameState, ai_wants_end: bool) -> str | None:
    """Decide whether the ride is over. The AI gets a vote, not a veto.

    Returns the end reason, or None to keep driving.
    """
    if (
        state.money_confidence >= CONFIDENCE_END_THRESHOLD
        and state.religion_confidence >= CONFIDENCE_END_THRESHOLD
    ):
        return END_BY_CONFIDENCE
    if state.message_count >= MAX_MESSAGES:
        return END_BY_MAX_MESSAGES
    if ai_wants_end and state.message_count >= SOFT_END_MESSAGES:
        return END_BY_AI
    return None


def apply_suggestion(state: GameState, suggestion: AISuggestion) -> GameState:
    """Fold one validated AI turn into the game state.

    Order matters: scores first, then the message counter, then the ending
    check - so the ending sees the numbers the player is about to see.
    """
    if state.game_status == "ended":
        return state

    _apply_scores(state, suggestion)
    state.message_count += 1

    state.current = Presentation(
        question=suggestion.question,
        thinking=suggestion.thinking,
        mood=suggestion.mood,
        driver_action=suggestion.driver_action,
    )
    state.conversation_history.append(
        Turn(role="abu_fadi", text=suggestion.question)
    )

    reason = evaluate_ending(state, suggestion.end_conversation)
    if reason is not None:
        state.game_status = "ended"
        state.end_reason = reason
    return state
