"""API request/response shapes.

Deliberately narrower than GameState: money_confidence and religion_confidence
never cross the wire. Abu Fadi's theory is the punchline, not a HUD readout.
"""

from pydantic import BaseModel, Field

from .engine import MAX_MESSAGES
from .models import DriverAction, GameState, GameStatus, Mood, Radar, Turn
from .service import MAX_ANSWER_LENGTH


class PublicState(BaseModel):
    session_id: str
    message_count: int
    max_messages: int = MAX_MESSAGES
    game_status: GameStatus
    end_reason: str | None = None
    radar: Radar
    question: str
    thinking: str
    mood: Mood
    driver_action: DriverAction
    history: list[Turn]
    #: True when the AI call failed and the scripted driver stood in.
    ai_degraded: bool = False

    @classmethod
    def from_state(cls, state: GameState, ai_degraded: bool = False) -> "PublicState":
        return cls(
            session_id=state.session_id,
            message_count=state.message_count,
            game_status=state.game_status,
            end_reason=state.end_reason,
            radar=state.radar,
            question=state.current.question,
            thinking=state.current.thinking,
            mood=state.current.mood,
            driver_action=state.current.driver_action,
            history=state.conversation_history,
            ai_degraded=ai_degraded,
        )


class StartRequest(BaseModel):
    """Nothing needed yet - kept so the contract can grow without a breaking change."""


class AnswerRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    answer: str = Field(min_length=1, max_length=MAX_ANSWER_LENGTH)
