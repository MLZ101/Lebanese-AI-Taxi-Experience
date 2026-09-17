"""Core types for The Lebanese Taxi Experience.

Two families of models live here:

1. Game state  - owned by the engine, never written to by the LLM.
2. AI contract - the *suggestions* the LLM is allowed to make.

Everything coming back from the LLM is treated as untrusted input, so the
AI-contract models coerce and clamp aggressively instead of blowing up.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --- Fixed vocabularies (these map 1:1 to UI assets, so no free-form values) ---

Mood = Literal["neutral", "curious", "suspicious", "excited", "upset"]
DriverAction = Literal["normal", "mirror", "nod", "money"]
GameStatus = Literal["active", "ended"]
Speaker = Literal["abu_fadi", "passenger"]

MOODS: tuple[str, ...] = ("neutral", "curious", "suspicious", "excited", "upset")
DRIVER_ACTIONS: tuple[str, ...] = ("normal", "mirror", "nod", "money")

DEFAULT_MOOD: Mood = "neutral"
DEFAULT_DRIVER_ACTION: DriverAction = "normal"

# Per-turn suggestion limits. Totals are clamped separately by the engine.
CHANGE_MIN = -10
CHANGE_MAX = 10
SCORE_MIN = 0
SCORE_MAX = 100


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _to_int(value: Any, default: int = 0) -> int:
    """Best-effort int coercion. The LLM likes to send "+3", 3.0 or "three"."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        try:
            return int(round(float(value.strip().replace("+", ""))))
        except ValueError:
            return default
    return default


# --------------------------------------------------------------------------- #
# Game state (engine-owned)
# --------------------------------------------------------------------------- #


class Radar(BaseModel):
    """Abu Fadi's mysterious dashboard. Values are 0-100, engine-owned."""

    money: int = 25
    status: int = 25
    suspicion: int = 15
    tip: int = 30


class Turn(BaseModel):
    role: Speaker
    text: str


class Presentation(BaseModel):
    """What the player currently sees / hears from Abu Fadi."""

    question: str
    thinking: str = ""
    mood: Mood = DEFAULT_MOOD
    driver_action: DriverAction = DEFAULT_DRIVER_ACTION


class GameState(BaseModel):
    """The whole truth about one taxi ride. Only the engine mutates this."""

    session_id: str
    message_count: int = 0
    money_confidence: int = 0
    religion_confidence: int = 0
    radar: Radar = Field(default_factory=Radar)
    conversation_history: list[Turn] = Field(default_factory=list)
    game_status: GameStatus = "active"
    current: Presentation
    # Set by the engine when the ride ends, so the UI knows *why* it ended.
    end_reason: str | None = None


# --------------------------------------------------------------------------- #
# AI contract (LLM-owned suggestions, untrusted)
# --------------------------------------------------------------------------- #


class RadarChanges(BaseModel):
    """Suggested radar deltas. Anything unusable becomes 0."""

    model_config = ConfigDict(extra="ignore")

    money: int = 0
    status: int = 0
    suspicion: int = 0
    tip: int = 0

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_and_clamp(cls, value: Any) -> int:
        return clamp(_to_int(value), CHANGE_MIN, CHANGE_MAX)


class AISuggestion(BaseModel):
    """The fixed JSON contract Abu Fadi must answer with.

    Only `question` is truly required: without a question there is no turn to
    show. Everything else degrades to a safe default rather than failing.
    """

    model_config = ConfigDict(extra="ignore")

    question: str
    thinking: str = ""
    mood: Mood = DEFAULT_MOOD
    driver_action: DriverAction = DEFAULT_DRIVER_ACTION
    radar_changes: RadarChanges = Field(default_factory=RadarChanges)
    money_confidence_change: int = 0
    religion_confidence_change: int = 0
    end_conversation: bool = False

    @field_validator("question", "thinking", mode="before")
    @classmethod
    def _clean_text(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("mood", mode="before")
    @classmethod
    def _safe_mood(cls, value: Any) -> str:
        text = str(value).strip().lower() if value is not None else ""
        return text if text in MOODS else DEFAULT_MOOD

    @field_validator("driver_action", mode="before")
    @classmethod
    def _safe_action(cls, value: Any) -> str:
        text = str(value).strip().lower() if value is not None else ""
        return text if text in DRIVER_ACTIONS else DEFAULT_DRIVER_ACTION

    @field_validator("radar_changes", mode="before")
    @classmethod
    def _safe_radar(cls, value: Any) -> Any:
        return value if isinstance(value, (dict, RadarChanges)) else {}

    @field_validator(
        "money_confidence_change", "religion_confidence_change", mode="before"
    )
    @classmethod
    def _safe_change(cls, value: Any) -> int:
        return clamp(_to_int(value), CHANGE_MIN, CHANGE_MAX)

    @field_validator("end_conversation", mode="before")
    @classmethod
    def _safe_flag(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "yes", "1"}
        return bool(value) if isinstance(value, (int, float)) else False

    @field_validator("question")
    @classmethod
    def _question_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("question must not be empty")
        return value
