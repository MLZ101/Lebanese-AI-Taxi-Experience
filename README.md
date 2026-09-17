# The Lebanese Taxi Experience

A short AI comedy game. You are in the back of Abu Fadi's taxi. He is nosy.

## Stack

- **Frontend** React + TypeScript + Vite + Tailwind + Framer Motion, styled as
  a 1997 arcade cabinet (Press Start 2P + VT323, self-hosted via Fontsource)
- **Backend** Python + FastAPI + Pydantic
- **AI** `gemini-3.5-flash-lite`, behind a small provider abstraction
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

## The look

Everything is hard-edged on purpose. The rules live in `frontend/src/index.css`
and are worth keeping:

- **No radius, no blur.** A global `* { border-radius: 0 }` enforces it. Depth
  comes from `.bevel` / `.bevel-in` / `.bevel-gold` - solid light/dark borders
  the way Win95 and every console menu of the era did it, never a soft shadow.
- **Stepped motion.** Animations use `steps(n)` so they read as frames rather
  than tweens. Same for the driver's camera moves, which are `ease: "linear"`
  over short durations.
- **Two fonts.** `font-pixel` (Press Start 2P) for chrome, labels and buttons -
  tiny sizes only, it is unreadable in a paragraph. `font-term` (VT323) for
  anything the player actually reads, at `text-lg` and up.
- **Palette sampled from the art.** `--color-taxi`, `--color-cab`, `--color-blood`
  and friends are lifted off `abu-fadi.jpeg`, so the chrome and the one piece of
  art look like they shipped together. Add colours there, not inline.
- **The page has margins.** `Cabinet` in `App.tsx` wraps everything in bezel →
  glass, with scanline, vignette and rolling-line overlays on top. All three are
  `pointer-events-none` and `aria-hidden`.
## Model choice

Picked in the UI before the ride starts; a session keeps its model for the whole
conversation. `GET /ai/models` returns the catalog, each row flagged available
or not. An unknown id falls back to a usable one instead of failing.

Measured over a fixed 4-turn ride:

| model | p50 | notes |
|---|---|---|
| `gemini-3.5-flash-lite` | **2.18s** | default |
| `gemini-3.1-flash-lite` | 3.32s | |
| `gemini-3-flash-preview` | - | bigger model |
| `fallback` | instant | scripted, no AI |

Adding a model is one row in `backend/app/ai/catalog.py`. Any provider failure
falls through to the scripted driver rather than stalling the ride.

## Abu Fadi's two threads

He is working out two things and he alternates between them: how much money the
passenger has, and which ta2ifa they are. The second one he gets at **bel
ta7ayol** - never by asking. He asks the innocent questions a nosy driver asks
anybody (the village, the family name, the school, where they go at the 3id) and
treats every answer as enormous evidence.

He is forbidden from asking outright or saying anything while they are still in
the car. He names his guess **once**, at the reveal, as the passenger is getting
out - and it stays a guess: the player answers `sa7` or `ghalat` and he has a
line ready either way. He does not take being wrong well.

His reasoning is deliberately rubbish, and he is warm about everyone. That gap -
nonsense evidence, total certainty - is the joke.

## Endings

The engine decides, never the LLM. In `backend/app/engine.py`:

| rule | constant | fires |
|---|---|---|
| early reveal - background theory alone | `EARLY_REVEAL_CONFIDENCE = 90` | any turn |
| both theories confident | `CONFIDENCE_END_THRESHOLD = 70` | any turn |
| Abu Fadi asks to stop | `SOFT_END_MESSAGES = 7` | turn 7+ |
| hard ceiling | `MAX_MESSAGES = 10` | turn 10 |

In practice rides end on the third rule around turn 7-8. The confidence-based
rules are tuned higher than the model's self-reported numbers actually reach -
see the measurement note beside `EARLY_REVEAL_CONFIDENCE`.

Once a ride ends the engine asks for a **verdict** - a second, differently
shaped LLM call producing his named guess, both reactions, his conclusions, the
ridiculous evidence, the fare and a closing line. If that call fails, a scripted
verdict stands in, and a blank `guess` is backfilled: losing the payoff is the
one failure a player would really notice.

## The radar

Four gauges, built as the instrument cluster of an early-2000s car: moulded
plastic, a strip of brushed aluminium, chrome rings, scale ticks, a red zone at
the top of every scale, and a needle with mass that overshoots the reading and
settles back. The cluster fades up as the ride goes on, from barely lit to hard
to ignore, like dash lights coming up as it gets dark.

**Still no numbers**, but each dial is now named. It began fully unlabelled -
the player was told nothing - and that turned out to be too hidden to be fun:
an icon can say *money*, but nothing short of a word separates "how rich he
thinks you are" from "what he expects to be handed at the end". So every dial
carries an etched pictogram plus one engraved word, MONEY / STATUS / DOUBT /
TIP, coloured to match its own needle arc. Real clusters label FUEL and TEMP;
this one does the same.

The pictograms are pixel grids in `frontend/src/components/dashIcons.ts`, not
an icon font - emoji and icon fonts would be the only smooth thing on screen.
Each grid is exactly 9x9 and must be drawn at a whole multiple of 9 px (27, 36),
or the cell edges land on half pixels and the icon turns to mush.

Values are 0-100 and engine-owned; see `backend/app/models.py`.

## Thinking out loud

Abu Fadi's `thinking` gets the same billing as the thing he actually says: its
own panel above the dialogue box, same text size, dashed border where the
speech box is solid, and the whole panel takes the colour of his mood.

It types itself out. Nothing is genuinely streaming - the backend sends the
whole turn in one response - so `useTypewriter` replays it character by
character, which is what makes him look like he is working the thought out
rather than having had it ready. A turn therefore reads thought-then-answer:
the question is withheld until the thought finishes, and the answer box stays
locked that whole time so nobody replies to a question still off screen.

Two things follow from that gating, and both matter if you touch this:

- The hook force-completes on a timer well after it should have ended. The
  question *and* the input are both waiting on `done`, so a stalled interval
  would soft-lock the ride rather than just skip an animation.
- While the request is merely in flight, the previous question stays on screen
  dimmed rather than vanishing - only a *new* thought mid-type hides it.

Under `prefers-reduced-motion` the whole string appears at once and every gate
opens immediately.

## Driver reactions

Mood is the only reaction signal - it drives both the colour of the cabin and
what Abu Fadi's body does. There is a single piece of art, so the five moods are
camera moves over it (a glance at the mirror, turning to study you, a greedy
flare) rather than separate frames. If real frames turn up, only `MOOD_MOTION`
in `TaxiView.tsx` needs to change.

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
backend/app/ai/          base, gemini, fallback, catalog (the model list)
backend/tests/           77 tests

frontend/src/types.ts      mirrors PublicState - keep in sync
frontend/src/api/client.ts typed fetch + ApiError
frontend/src/hooks/useGame.ts  the entire client state
frontend/src/hooks/useTypewriter.ts  replays a string one character at a time
frontend/src/components/   TitleScreen (the attract screen)
                           TaxiView (the back seat + driver reactions)
                           RadarPanel (the dial cluster), dashIcons, PixelIcon
                           ThinkingPanel (the thought, typing itself out)
                           QuestionPanel (the dialogue box), AnswerInput,
                           HistoryLog
                           RevealScreen (the Tawa2ef payoff)
                           ModelPicker (which brain drives)
frontend/src/assets/       abu-fadi.jpeg - the one piece of art
```
