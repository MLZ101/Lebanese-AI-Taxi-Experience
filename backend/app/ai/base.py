"""Provider-agnostic pieces: the interface, prompt assembly, JSON parsing.

A new provider (Groq, OpenAI, whatever) only has to implement the HTTP call -
prompt building and response validation are shared here.
"""

from __future__ import annotations

import json
import re
from typing import Protocol

from pydantic import ValidationError

from ..models import AISuggestion, GameState
from ..prompts import SYSTEM_PROMPT, build_briefing


class AIError(RuntimeError):
    """Any failure to get a usable suggestion: HTTP, timeout, bad JSON, junk."""


class AIProvider(Protocol):
    name: str

    async def suggest(self, state: GameState) -> AISuggestion:
        """Return Abu Fadi's next turn, or raise AIError."""
        ...


def system_text(state: GameState) -> str:
    return SYSTEM_PROMPT + build_briefing(state)


def transcript(state: GameState) -> list[dict[str, str]]:
    """History as neutral {role, text} pairs; providers map roles themselves."""
    return [
        {"role": "assistant" if t.role == "abu_fadi" else "user", "text": t.text}
        for t in state.conversation_history
    ]


_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def _extract_json(raw: str) -> dict:
    """Pull one JSON object out of whatever the model actually sent back."""
    text = _FENCE.sub("", (raw or "").strip())
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Models sometimes wrap the object in a sentence. Take the outermost
        # brace pair and try again.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise AIError("no JSON object in model response")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AIError(f"unparseable JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise AIError("model response was not a JSON object")
    return parsed


def parse_suggestion(raw: str) -> AISuggestion:
    """Untrusted text in, validated suggestion out."""
    try:
        return AISuggestion.model_validate(_extract_json(raw))
    except ValidationError as exc:
        raise AIError(f"response failed validation: {exc.error_count()} error(s)") from exc
