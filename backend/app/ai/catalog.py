"""Which brains Abu Fadi can be given, and how to build one.

Adding a model is one row here. A model whose provider has no API key is still
listed, marked unavailable, so the UI can grey it out rather than pretend it
does not exist.
"""

from __future__ import annotations

from .. import config
from .base import AIError, AIProvider
from .fallback import FallbackProvider
from .azure_openai import AzureOpenAIProvider
from .gemini import GeminiProvider
from .openai_api import OpenAIProvider

#: id is the provider's own model name - it is passed through verbatim.
#: Notes come from measured 4-turn rides. Dropped after measuring:
#: gpt-5-mini (timed out 4/4), gpt-5.4-nano and gpt-5.6-luna both slip out of
#: Latin letters into Arabic script mid-sentence, which breaks the look.
MODELS: list[dict[str, str]] = [
    {
        "id": "gemini-3.5-flash-lite",
        "label": "Gemini 3.5 Flash-Lite",
        "provider": "gemini",
        "note": "fastest, ~2s a turn",
    },
    {
        "id": "gemini-3.1-flash-lite",
        "label": "Gemini 3.1 Flash-Lite",
        "provider": "gemini",
        "note": "slower, ~3.3s a turn",
    },
    {
        "id": "gemini-3-flash-preview",
        "label": "Gemini 3 Flash",
        "provider": "gemini",
        "note": "bigger model",
    },
    {
        "id": "gpt-5.4-mini",
        "label": "GPT-5.4 mini",
        "provider": "openai",
        "note": "OpenAI, fastest of all (~1.3s)",
    },
    {
        "id": "gpt-5.6-luna",
        "label": "GPT-5.6 Luna",
        "provider": "openai",
        "note": "OpenAI, ~2.8s",
    },
    {
        "id": "gpt-5.5",
        "label": "GPT-5.5",
        "provider": "openai",
        "note": "OpenAI, best writing but slow (~8.5s)",
    },
    {
        "id": "azure/gpt-5.5",
        "label": "GPT-5.5 (Azure)",
        "provider": "azure",
        "note": "your Azure deployment",
    },
    {
        "id": "fallback",
        "label": "Scripted driver",
        "provider": "fallback",
        "note": "no AI, always works",
    },
]

_KEYS = {
    "gemini": lambda: bool(config.GEMINI_API_KEY),
    "openai": lambda: bool(config.OPENAI_API_KEY),
    # A key alone points at nothing on Azure - we also need to know which
    # resource and which deployment, from either the Target URI or the pieces.
    "azure": lambda: bool(config.AZURE_OPENAI_API_KEY) and _azure_addressed(),
    "fallback": lambda: True,
}

_BUILDERS = {
    "gemini": lambda model: GeminiProvider(model=model),
    "openai": lambda model: OpenAIProvider(model=model),
    # The catalog id is just a label here - the deployment name comes from env.
    "azure": lambda model: AzureOpenAIProvider(),
    "fallback": lambda model: FallbackProvider(),
}


def _azure_addressed() -> bool:
    """Do we know the resource and the deployment, however they were given?"""
    from .azure_openai import parse_target_uri

    from_uri = parse_target_uri(config.AZURE_OPENAI_TARGET_URI)
    endpoint = config.AZURE_OPENAI_ENDPOINT or from_uri.get("endpoint")
    deployment = config.AZURE_OPENAI_DEPLOYMENT or from_uri.get("deployment")
    return bool(endpoint and deployment)


def is_available(entry: dict) -> bool:
    return _KEYS.get(entry["provider"], lambda: False)()


def default_model_id() -> str:
    """The configured model, if it is one we know about."""
    if config.AI_PROVIDER == "fallback":
        return "fallback"
    if config.AI_PROVIDER == "openai":
        for entry in MODELS:
            if entry["id"] == config.OPENAI_MODEL and is_available(entry):
                return entry["id"]
    if config.AI_PROVIDER == "azure":
        azure = next(e for e in MODELS if e["provider"] == "azure")
        if is_available(azure):
            return azure["id"]
    for entry in MODELS:
        if entry["id"] == config.GEMINI_MODEL and is_available(entry):
            return entry["id"]
    return next((e["id"] for e in MODELS if is_available(e)), "fallback")


def listing() -> list[dict]:
    """Catalog for the UI, each row flagged available or not."""
    return [{**e, "available": is_available(e)} for e in MODELS]


def resolve(model_id: str | None) -> str:
    """Pick a usable model id, falling back rather than failing."""
    if model_id:
        for entry in MODELS:
            if entry["id"] == model_id and is_available(entry):
                return model_id
    return default_model_id()


_cache: dict[str, AIProvider] = {}


def provider_for(model_id: str) -> AIProvider:
    """Build (and reuse) the provider behind a model id."""
    if model_id not in _cache:
        entry = next((e for e in MODELS if e["id"] == model_id), None)
        if entry is None or not is_available(entry):
            raise AIError(f"model {model_id!r} is not available")
        _cache[model_id] = _BUILDERS[entry["provider"]](model_id)
    return _cache[model_id]
