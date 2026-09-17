# The Lebanese Taxi Experience

A short AI comedy game. You are in the back of Abu Fadi's taxi. He is nosy.

## Stack

- **Frontend** React + TypeScript + Vite + Tailwind + Framer Motion
- **Backend** Python + FastAPI + Pydantic
- **AI** Gemini 3 Flash-Lite, behind a small provider abstraction
- **State** in-memory sessions, no database

## Architecture

```
React -> FastAPI -> Game Engine -> AI Provider -> Pydantic validation
                 -> Game Engine applies validated changes -> React
```

The LLM only ever *suggests* (next question, reaction, mood, deltas). The game
engine owns every actual number: counters, radar, confidence, ending rules.

## Backend

```bash
cd backend
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
cp .env.example .env          # then paste your GEMINI_API_KEY
./.venv/Scripts/python.exe -m pytest tests -q
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Interactive docs at <http://localhost:8000/docs>.

## Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Vite proxies `/game` and `/health` to `127.0.0.1:8000`, so run the backend too.
No state library - one `useGame` hook holds the whole game.

## The radar

Four meters, no labels and no numbers - the player is never told what is being
measured. The panel also fades up as the ride goes on, from barely lit to hard
to ignore. Meanings live in `backend/app/models.py`; keep them there.

## Driver reactions

There is a single piece of art, so Abu Fadi's four `driver_action` states are
camera moves over it (lean to the mirror, a nod, a greedy flare) rather than
separate frames. If real frames turn up, only `ACTION_MOTION` in
`TaxiView.tsx` needs to change.

Framer Motion drives those reactions; everything the player must *read* is
animated in CSS instead, with the base style already the finished state. A
broken animation layer can cost a flourish, never the game.

## API

| Endpoint | Does |
|---|---|
| `GET /health` | provider, model, live session count |
| `POST /game/start` | opens a ride, returns Abu Fadi's first question |
| `POST /game/answer` | `{session_id, answer}` -> one full turn |

`404` unknown session, `409` ride already ended, `422` empty/oversized answer.
A provider failure is **not** an error: the scripted driver takes over and the
response carries `ai_degraded: true`.

`money_confidence` and `religion_confidence` are never part of the game state on
the wire. Setting `EXPOSE_DEBUG=true` in `backend/.env` adds them in a separate
`debug` block - useful when tuning the prompt, spoilers otherwise. Off by
default, and there is a test pinning that the scores never appear at the top
level even when it is on.

## Layout

```
backend/app/models.py    game state + the AI JSON contract (untrusted input)
backend/app/engine.py    rules, clamping, ending conditions (pure, sync)
backend/app/service.py   one turn: answer -> AI -> validate -> apply
backend/app/sessions.py  in-memory session store
backend/app/schemas.py   API request/response shapes
backend/app/main.py      FastAPI app
backend/app/prompts.py   Abu Fadi persona + per-turn pacing briefing
backend/app/ai/          provider abstraction: base, gemini, fallback
backend/tests/           52 tests

frontend/src/types.ts      mirrors PublicState - keep in sync
frontend/src/api/client.ts typed fetch + ApiError
frontend/src/hooks/useGame.ts  the entire client state
frontend/src/components/   TaxiView (the back seat + driver reactions)
                           RadarPanel (the four unlabelled meters)
                           QuestionPanel, AnswerInput, ThinkingBubble, HistoryLog
frontend/src/assets/       abu-fadi.jpeg - the one piece of art
```
