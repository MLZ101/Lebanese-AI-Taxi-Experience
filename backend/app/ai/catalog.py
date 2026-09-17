"""Which brains Abu Fadi can be given, and how to build one.

Adding a model is one row here. A model whose provider has no API key is still
listed, marked unavailable, so the UI can grey it out rather than pretend it
does not exist.
"""

from __future__ import annotations

from .. import config
from .base import AIError, AIProvider
from .fallback import FallbackProvider
from .gemini import GeminiProvider

#: id must be Gemini's own model name - it is passed through verbatim.
#: Notes come from measured 4-turn rides.
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
        "id": "fallback",
        "label": "Scripted driver",
        "provider": "fallback",
        "note": "no AI, always works",
    },
]

_KEYS = {
    "gemini": lambda: bool(config.GEMINI_API_KEY),
    "fallback": lambda: True,
}

_BUILDERS = {
    "gemini": lambda model: GeminiProvider(model=model),
    "fallback": lambda model: FallbackProvider(),
}


def is_available(entry: dict) -> bool:
    return _KEYS.get(entry["provider"], lambda: False)()


def default_model_id() -> str:
    """The configured model, if it is one we know about."""
    if config.AI_PROVIDER == "fallback":
        return "fallback"
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
