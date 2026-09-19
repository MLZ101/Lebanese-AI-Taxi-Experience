"""Provider selection. Swapping models is a one-line env change, or a
per-session choice made in the UI - see catalog.py."""

from .. import config
from .azure_openai import AzureOpenAIProvider
from .base import AIError, AIProvider
from .catalog import (
    MODELS,
    default_model_id,
    is_available,
    listing,
    provider_for,
    resolve,
)
from .fallback import FallbackProvider, canned_suggestion, canned_verdict
from .gemini import GeminiProvider
from .openai_api import OpenAIProvider

__all__ = [
    "AIError",
    "AIProvider",
    "AzureOpenAIProvider",
    "FallbackProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "MODELS",
    "canned_suggestion",
    "canned_verdict",
    "default_model_id",
    "get_provider",
    "is_available",
    "listing",
    "provider_for",
    "resolve",
]


def get_provider(model_id: str | None = None) -> AIProvider:
    """The provider for a given model, or the configured default."""
    return provider_for(resolve(model_id))
