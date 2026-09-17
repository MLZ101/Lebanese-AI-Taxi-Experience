"""Environment-backed settings. Secrets live in backend/.env (gitignored)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

#: "gemini" or "fallback" (offline canned driver, handy for UI work).
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

AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "12"))
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
