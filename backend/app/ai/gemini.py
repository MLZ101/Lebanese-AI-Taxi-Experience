"""Gemini provider - plain REST over httpx, no SDK dependency."""

from __future__ import annotations

import asyncio

import httpx

from .. import config
from ..models import AISuggestion, GameState, Verdict
from .base import (
    AIError,
    parse_suggestion,
    parse_verdict,
    system_text,
    transcript,
    verdict_text,
)

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
        "radar_changes",
        "money_confidence_change",
        "religion_confidence_change",
        "end_conversation",
    ],
}


VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "guess": {"type": "string"},
        "money_verdict": {"type": "string"},
        "background_verdict": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "if_right": {"type": "string"},
        "if_wrong": {"type": "string"},
        "fare": {"type": "string"},
        "closing_line": {"type": "string"},
    },
    "required": [
        "guess",
        "money_verdict",
        "background_verdict",
        "evidence",
        "if_right",
        "if_wrong",
        "fare",
        "closing_line",
    ],
}


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        if not self.api_key:
            raise AIError("GEMINI_API_KEY is not set")

    #: Gemini rejects a conversation that ends on a model turn. At verdict time
    #: the last thing said is Abu Fadi's own question, so we hand him the cue
    #: he would actually get: the passenger arriving.
    ARRIVAL_CUE = "[Wselna. The passenger is getting out of the taxi.]"

    def _payload(self, state: GameState, system: str, schema: dict) -> dict:
        contents = [
            {"role": "model" if t["role"] == "assistant" else "user",
             "parts": [{"text": t["text"]}]}
            for t in transcript(state)
        ]
        if not contents or contents[-1]["role"] == "model":
            contents.append(
                {"role": "user", "parts": [{"text": self.ARRIVAL_CUE}]}
            )
        return {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 1.0,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
                "responseSchema": schema,
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

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        """How long to wait before trying again.

        Rate limits need real patience; everything else just needs a beat.
        """
        if response is not None and response.status_code == 429:
            header = response.headers.get("retry-after")
            if header:
                try:
                    return min(float(header), 8.0)
                except ValueError:
                    pass
            return 2.0 * (attempt + 1)
        return 0.6 * (attempt + 1)

    async def _call(self, state: GameState, system: str, schema: dict) -> str:
        """One request, retried. Both kinds of call go through here."""
        url = f"{config.GEMINI_BASE_URL}/models/{self.model}:generateContent"
        last: Exception | None = None

        for attempt in range(config.AI_MAX_RETRIES + 1):
            response = None
            try:
                async with httpx.AsyncClient(timeout=config.AI_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        url,
                        headers={
                            "x-goog-api-key": self.api_key,
                            "Content-Type": "application/json",
                        },
                        json=self._payload(state, system, schema),
                    )
                if response.status_code != 200:
                    raise AIError(
                        f"gemini HTTP {response.status_code}: {response.text[:200]}"
                    )
                return self._text_from(response.json())
            except (AIError, httpx.HTTPError, ValueError) as exc:
                last = exc
                if attempt < config.AI_MAX_RETRIES:
                    await asyncio.sleep(self._retry_delay(response, attempt))

        raise AIError(f"gemini request failed: {type(last).__name__}: {last}")

    async def suggest(self, state: GameState) -> AISuggestion:
        return parse_suggestion(
            await self._call(state, system_text(state), RESPONSE_SCHEMA)
        )

    async def verdict(self, state: GameState) -> Verdict:
        return parse_verdict(
            await self._call(state, verdict_text(state), VERDICT_SCHEMA)
        )
