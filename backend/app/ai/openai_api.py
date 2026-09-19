"""OpenAI provider, on the official SDK.

The SDK owns the transport: connection pooling, timeouts and retry/backoff
(including Retry-After on 429s) all come from the client, so this file is just
prompt in, validated suggestion out.

Set in backend/.env:
    OPENAI_API_KEY=sk-...

Pointing OPENAI_BASE_URL elsewhere makes the same client work with any
OpenAI-compatible service (Groq, OpenRouter, a local server).
"""

from __future__ import annotations

import re

from openai import AsyncOpenAI, BadRequestError, OpenAIError

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

#: Newer models reject some of the older knobs. When the API names a parameter
#: it will not accept, we drop it and try again rather than failing the turn.
_UNSUPPORTED = re.compile(
    r"'?(max_tokens|temperature|top_p|max_completion_tokens)'?", re.I
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = config.OPENAI_API_KEY if api_key is None else api_key
        if not key:
            raise AIError("OPENAI_API_KEY is not set")
        self.model = model or config.OPENAI_MODEL
        self.client = AsyncOpenAI(
            api_key=key,
            base_url=config.OPENAI_BASE_URL or None,
            timeout=config.AI_TIMEOUT_SECONDS,
            max_retries=config.AI_MAX_RETRIES,
        )

    def _kwargs(self, state: GameState, system: str) -> dict:
        messages = [{"role": "system", "content": system}]
        messages += [
            {"role": t["role"], "content": t["text"]} for t in transcript(state)
        ]
        return {
            "model": self.model,
            "messages": messages,
            # Newer models want max_completion_tokens; if this one refuses it,
            # _drop_unsupported takes it back out and we try again.
            "max_completion_tokens": 2048,
            # Guarantees parseable JSON; our own validation still runs after.
            "response_format": {"type": "json_object"},
        }

    @staticmethod
    def _drop_unsupported(kwargs: dict, message: str) -> dict | None:
        """Remove whatever parameter the API just complained about."""
        found = _UNSUPPORTED.findall(message or "")
        removed = {f.strip("'") for f in found} & set(kwargs)
        if not removed:
            return None
        return {k: v for k, v in kwargs.items() if k not in removed}

    @staticmethod
    def _text_from(completion) -> str:
        choices = getattr(completion, "choices", None) or []
        if not choices:
            raise AIError("no choices returned")
        text = (choices[0].message.content or "").strip()
        if not text:
            raise AIError(f"empty response (finish: {choices[0].finish_reason})")
        return text

    async def _call(self, state: GameState, system: str) -> str:
        kwargs = self._kwargs(state, system)
        try:
            completion = await self.client.chat.completions.create(**kwargs)
        except BadRequestError as exc:
            # One retry without the parameter it objected to. Anything else is
            # a real error - a bad model name, a content filter - so it raises.
            trimmed = self._drop_unsupported(kwargs, str(exc))
            if trimmed is None:
                raise AIError(f"openai rejected the request: {exc}") from exc
            try:
                completion = await self.client.chat.completions.create(**trimmed)
            except OpenAIError as retry_exc:
                raise AIError(
                    f"openai request failed: {type(retry_exc).__name__}: {retry_exc}"
                ) from retry_exc
        except OpenAIError as exc:
            # The SDK has already retried timeouts and 429s by this point.
            raise AIError(f"openai request failed: {type(exc).__name__}: {exc}") from exc

        return self._text_from(completion)

    async def suggest(self, state: GameState) -> AISuggestion:
        return parse_suggestion(await self._call(state, system_text(state)))

    async def verdict(self, state: GameState) -> Verdict:
        return parse_verdict(await self._call(state, verdict_text(state)))
