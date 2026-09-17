"""Provider selection. Swapping models is a one-line env change."""

from .. import config
from .base import AIError, AIProvider
from .fallback import FallbackProvider, canned_suggestion
from .gemini import GeminiProvider

__all__ = [
    "AIError",
    "AIProvider",
    "FallbackProvider",
    "GeminiProvider",
    "canned_suggestion",
    "get_provider",
]

_provider: AIProvider | None = None


def get_provider() -> AIProvider:
    """Build the configured provider once and reuse it."""
    global _provider
    if _provider is None:
        if config.AI_PROVIDER == "gemini":
            _provider = GeminiProvider()
        else:
            _provider = FallbackProvider()
    return _provider
