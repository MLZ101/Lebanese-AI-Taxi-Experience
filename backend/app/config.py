"""Environment-backed settings. Secrets live in backend/.env (gitignored)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

#: "gemini", "openai", "azure", or "fallback" (offline canned driver).
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
GEMINI_BASE_URL = os.getenv(
    "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
).strip()

#: Exposes Abu Fadi's hidden theory scores to the client in a `debug` block.
#: Off by default - seeing the scores gives away the ending. Turn it on while
#: tuning the prompt, when you need to watch the confidences move.
EXPOSE_DEBUG = os.getenv("EXPOSE_DEBUG", "false").strip().lower() in {"1", "true", "yes"}

# OpenAI (api.openai.com). Point OPENAI_BASE_URL elsewhere for any
# OpenAI-compatible service.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()

# Azure OpenAI. The deployment name is what identifies the model, not a
# model field - see app/ai/azure_openai.py.
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
# Easiest: paste the "Target URI" Azure shows next to the deployment - it
# already contains the endpoint, the deployment name and the api-version.
AZURE_OPENAI_TARGET_URI = os.getenv("AZURE_OPENAI_TARGET_URI", "").strip()
# Or set the pieces yourself. These win over the Target URI when both are given.
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "").strip()
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "").strip()

AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "12"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
