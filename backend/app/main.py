"""FastAPI surface. Two endpoints, no more than the game needs."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config, service
from .ai import listing
from .schemas import AnswerRequest, PublicState, StartRequest
from .sessions import store

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="The Lebanese Taxi Experience", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "provider": config.AI_PROVIDER,
        "model": config.GEMINI_MODEL,
        "active_sessions": len(store),
    }


@app.get("/ai/models")
def models() -> dict:
    """Which brains can drive, and which have a key configured."""
    return {"models": listing()}


@app.post("/game/start", response_model=PublicState)
def start_game(request: StartRequest | None = None) -> PublicState:
    """Open a ride and hand back Abu Fadi's first question."""
    chosen = request.model if request else None
    return PublicState.from_state(service.start_game(store, chosen))


@app.post("/game/answer", response_model=PublicState)
async def answer(request: AnswerRequest) -> PublicState:
    """Play one turn: the passenger answers, Abu Fadi responds."""
    try:
        state, degraded = await service.submit_answer(
            store, request.session_id, request.answer
        )
    except service.SessionNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.GameAlreadyEnded as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.InvalidAnswer as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PublicState.from_state(state, ai_degraded=degraded)
