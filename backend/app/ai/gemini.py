"""Gemini provider - plain REST over httpx, no SDK dependency."""

from __future__ import annotations

import asyncio

import httpx

from .. import config
from ..models import AISuggestion, GameState
from .base import AIError, parse_suggestion, system_text, transcript

#: Mirrors the AI contract so the model is nudged into shape before our own
#: validation runs. Belt and braces - we still never trust the output.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "thinking": {"type": "string"},
        "mood": {
            "type": "string",
            "enum": ["neutral", "curious", "suspicious", "excited", "upset"],
        },
        "driver_action": {
            "type": "string",
            "enum": ["normal", "mirror", "nod", "money"],
        },
        "radar_changes": {
            "type": "object",
            "properties": {
                "money": {"type": "integer"},
                "status": {"type": "integer"},
                "suspicion": {"type": "integer"},
                "tip": {"type": "integer"},
            },
            "required": ["money", "status", "suspicion", "tip"],
        },
        "money_confidence_change": {"type": "integer"},
        "religion_confidence_change": {"type": "integer"},
        "end_conversation": {"type": "boolean"},
    },
    "required": [
        "question",
        "thinking",
        "mood",
        "driver_action",
        "radar_changes",
        "money_confidence_change",
        "religion_confidence_change",
        "end_conversation",
    ],
}


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        if not self.api_key:
            raise AIError("GEMINI_API_KEY is not set")

    def _payload(self, state: GameState) -> dict:
        contents = [
            {"role": "model" if t["role"] == "assistant" else "user",
             "parts": [{"text": t["text"]}]}
            for t in transcript(state)
        ]
        return {
            "systemInstruction": {"parts": [{"text": system_text(state)}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 1.0,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
                "responseSchema": RESPONSE_SCHEMA,
            },
        }

    @staticmethod
    def _text_from(data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            blocked = (data.get("promptFeedback") or {}).get("blockReason")
            raise AIError(f"no candidates returned{f' ({blocked})' if blocked else ''}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise AIError(f"empty response (finish: {candidates[0].get('finishReason')})")
        return text

    async def suggest(self, state: GameState) -> AISuggestion:
        url = f"{config.GEMINI_BASE_URL}/models/{self.model}:generateContent"
        last: Exception | None = None

        for attempt in range(config.AI_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=config.AI_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        url,
                        headers={
                            "x-goog-api-key": self.api_key,
                            "Content-Type": "application/json",
                        },
                        json=self._payload(state),
                    )
                if response.status_code != 200:
                    raise AIError(
                        f"gemini HTTP {response.status_code}: {response.text[:200]}"
                    )
                return parse_suggestion(self._text_from(response.json()))
            except (AIError, httpx.HTTPError, ValueError) as exc:
                last = exc
                if attempt < config.AI_MAX_RETRIES:
                    await asyncio.sleep(0.6 * (attempt + 1))

        raise AIError(f"gemini request failed: {last}")
