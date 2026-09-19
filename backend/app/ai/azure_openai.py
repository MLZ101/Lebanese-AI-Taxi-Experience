"""Azure OpenAI provider.

OpenAI-shaped, with three differences that catch people out:
  - auth is an `api-key` header, not `Authorization: Bearer`
  - the model is the *deployment name* in the URL, not a field in the body
  - the URL carries an `api-version` query parameter

The easy way to configure it is to paste the key and the "Target URI" that
Azure shows next to your deployment - the endpoint, the deployment name and the
api-version are all already in that one string:

    AZURE_OPENAI_API_KEY=...
    AZURE_OPENAI_TARGET_URI=https://my-res.openai.azure.com/openai/deployments/my-gpt/chat/completions?api-version=2025-01-01-preview

Setting the three parts separately also works, and wins if both are given:

    AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
    AZURE_OPENAI_DEPLOYMENT=<your deployment name>
    AZURE_OPENAI_API_VERSION=2024-10-21
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import parse_qs, urlparse

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

#: Used only when neither the env nor the Target URI names one.
DEFAULT_API_VERSION = "2024-10-21"

#: Newer models reject some of the older knobs. When Azure names a parameter it
#: will not accept, we drop it and try once more rather than failing the turn.
_UNSUPPORTED = re.compile(
    r"'?(max_tokens|temperature|top_p|max_completion_tokens)'?", re.I
)


def parse_target_uri(uri: str) -> dict[str, str]:
    """Pull endpoint, deployment and api-version out of Azure's Target URI.

    Azure shows one long URL next to a deployment and it already contains
    everything, so pasting that beats copying three fields by hand.
    Returns whatever it could find; missing pieces are simply absent.
    """
    found: dict[str, str] = {}
    if not uri:
        return found
    parsed = urlparse(uri.strip())
    if parsed.scheme and parsed.netloc:
        found["endpoint"] = f"{parsed.scheme}://{parsed.netloc}"
    match = re.search(r"/deployments/([^/?#]+)", parsed.path)
    if match:
        found["deployment"] = match.group(1)
    version = parse_qs(parsed.query).get("api-version")
    if version and version[0]:
        found["api_version"] = version[0]
    return found


class AzureOpenAIProvider:
    name = "azure"

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
    ):
        self.api_key = (
            config.AZURE_OPENAI_API_KEY if api_key is None else api_key
        )
        # Anything given explicitly wins; the Target URI fills in the rest.
        from_uri = parse_target_uri(config.AZURE_OPENAI_TARGET_URI)
        self.endpoint = (
            endpoint or config.AZURE_OPENAI_ENDPOINT or from_uri.get("endpoint", "")
        ).rstrip("/")
        self.deployment = (
            deployment
            or config.AZURE_OPENAI_DEPLOYMENT
            or from_uri.get("deployment", "")
        )
        self.api_version = (
            api_version
            or config.AZURE_OPENAI_API_VERSION
            or from_uri.get("api_version", "")
            or DEFAULT_API_VERSION
        )
        self.model = self.deployment
        if not self.api_key:
            raise AIError("AZURE_OPENAI_API_KEY is not set")
        if not self.endpoint:
            raise AIError(
                "AZURE_OPENAI_ENDPOINT is not set "
                "(or paste AZURE_OPENAI_TARGET_URI instead)"
            )
        if not self.deployment:
            raise AIError(
                "AZURE_OPENAI_DEPLOYMENT is not set "
                "(or paste AZURE_OPENAI_TARGET_URI instead)"
            )

    @property
    def url(self) -> str:
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )

    def _payload(self, state: GameState, system: str) -> dict:
        messages = [{"role": "system", "content": system}]
        messages += [
            {"role": t["role"], "content": t["text"]} for t in transcript(state)
        ]
        return {
            "messages": messages,
            # Newer deployments want max_completion_tokens; if this one refuses
            # it, _drop_unsupported takes it back out and we retry.
            "max_completion_tokens": 2048,
            # Guarantees parseable JSON; our own validation still runs after.
            "response_format": {"type": "json_object"},
        }

    @staticmethod
    def _drop_unsupported(payload: dict, message: str) -> dict | None:
        """Remove whatever parameter Azure just complained about."""
        found = _UNSUPPORTED.findall(message or "")
        removed = {f.strip("'") for f in found} & set(payload)
        if not removed:
            return None
        trimmed = {k: v for k, v in payload.items() if k not in removed}
        return trimmed

    @staticmethod
    def _text_from(data: dict) -> str:
        if "error" in data and not data.get("choices"):
            raise AIError(str(data["error"])[:200])
        choices = data.get("choices") or []
        if not choices:
            raise AIError("no choices returned")
        text = ((choices[0].get("message") or {}).get("content") or "").strip()
        if not text:
            raise AIError(f"empty response (finish: {choices[0].get('finish_reason')})")
        return text

    @staticmethod
    def _retry_delay(response: httpx.Response | None, attempt: int) -> float:
        if response is not None and response.status_code == 429:
            header = response.headers.get("retry-after")
            if header:
                try:
                    return min(float(header), 8.0)
                except ValueError:
                    pass
            return 2.0 * (attempt + 1)
        return 0.6 * (attempt + 1)

    async def _call(self, state: GameState, system: str) -> str:
        payload = self._payload(state, system)
        last: Exception | None = None

        for attempt in range(config.AI_MAX_RETRIES + 2):
            response = None
            try:
                async with httpx.AsyncClient(timeout=config.AI_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        self.url,
                        headers={
                            "api-key": self.api_key,
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                if response.status_code == 400:
                    trimmed = self._drop_unsupported(payload, response.text)
                    if trimmed is not None:
                        payload = trimmed
                        continue  # same attempt budget, simpler request
                if response.status_code != 200:
                    raise AIError(
                        f"azure HTTP {response.status_code}: {response.text[:200]}"
                    )
                return self._text_from(response.json())
            except (AIError, httpx.HTTPError, ValueError) as exc:
                last = exc
                if attempt < config.AI_MAX_RETRIES:
                    await asyncio.sleep(self._retry_delay(response, attempt))
                else:
                    break

        raise AIError(f"azure request failed: {type(last).__name__}: {last}")

    async def suggest(self, state: GameState) -> AISuggestion:
        return parse_suggestion(await self._call(state, system_text(state)))

    async def verdict(self, state: GameState) -> Verdict:
        return parse_verdict(await self._call(state, verdict_text(state)))
