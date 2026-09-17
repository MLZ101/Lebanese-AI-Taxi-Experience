import type { ReactNode } from "react";

import { AnswerInput } from "./components/AnswerInput";
import { HistoryLog } from "./components/HistoryLog";
import { QuestionPanel } from "./components/QuestionPanel";
import { RadarPanel } from "./components/RadarPanel";
import { TaxiView } from "./components/TaxiView";
import { ThinkingPanel } from "./components/ThinkingPanel";
import { TitleScreen } from "./components/TitleScreen";
import { useGame } from "./hooks/useGame";
import { useTypewriter } from "./hooks/useTypewriter";

export default function App() {
  const { state, phase, error, waiting, canAnswer, start, answer } = useGame();

  /*
   * Abu Fadi thinks out loud before he speaks. The thought types itself out
   * first and the question only lands once it finishes, so a turn reads
   * thought-then-answer instead of arriving all at once.
   */
  const thinking = useTypewriter(
    state?.thinking ?? "",
    state?.message_count ?? 0,
  );
  /** A new thought is still landing, so he has not got to the question yet. */
  const streaming = !waiting && !thinking.done;

  return (
    <Cabinet>
      {/*
       * No state yet means the ride never started - including when start
       * failed, so the player can try again instead of staring at a locked
       * screen.
       */}
      {!state ? (
        <TitleScreen
          onStart={start}
          starting={phase === "starting"}
          error={error}
        />
      ) : (
        <div className="flex h-full min-h-0 flex-col">
          <Hud
            count={state.message_count}
            max={state.max_messages}
            ended={state.game_status === "ended"}
          />

          <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
            {/* Left: the back seat, with Abu Fadi's dashboard bolted under. */}
            <section className="pix-scroll flex min-h-0 shrink-0 flex-col gap-2 overflow-y-auto p-2 sm:gap-3 sm:p-3 lg:w-[46%] lg:shrink lg:flex-1">
              <div className="bevel p-1">
                <TaxiView
                  mood={state.mood}
                  action={state.driver_action}
                  turn={state.message_count}
                />
              </div>
              {/* Bolted to the bottom of the dash, so the column has no
                  dead space under it on a wide screen. */}
              <div className="lg:mt-auto">
                <RadarPanel
                  radar={state.radar}
                  messageCount={state.message_count}
                />
              </div>
            </section>

            {/* Right: the conversation. */}
            <section className="flex min-h-0 w-full flex-col gap-2 border-t-4 border-cab-hi p-2 sm:gap-3 sm:p-3 lg:max-w-2xl lg:border-t-0 lg:border-l-4">
              <HistoryLog history={state.history} />

              <div className="space-y-2 sm:space-y-3">
                <ThinkingPanel
                  shown={thinking.shown}
                  done={thinking.done}
                  mood={state.mood}
                  waiting={waiting}
                />

                <QuestionPanel
                  question={state.question}
                  turn={state.message_count}
                  ready={!streaming}
                  dimmed={waiting}
                />

                {error && (
                  <p className="bevel-in px-3 py-2 font-term text-lg text-blood">
                    ! {error}
                  </p>
                )}

                {state.game_status === "ended" ? (
                  <RideOver />
                ) : (
                  <AnswerInput
                    // Stays locked until the question is actually on screen,
                    // so nobody answers a question they cannot read yet.
                    disabled={!canAnswer || streaming}
                    waiting={waiting}
                    onSubmit={answer}
                  />
                )}

                {state.ai_degraded && (
                  <p className="font-pixel text-[7px] leading-relaxed text-khaki">
                    ⚠ RADIO STATIC — ABU FADI KEPT TALKING ANYWAY
                  </p>
                )}
              </div>
            </section>
          </div>
        </div>
      )}
    </Cabinet>
  );
}

/**
 * The machine the game is running on.
 *
 * Margins on all four sides, a bezel, then the glass - so the page reads as a
 * screen sitting in a room rather than a website filling a window. The CRT
 * layers on top are decorative and never take pointer events.
 */
function Cabinet({ children }: { children: ReactNode }) {
  return (
    <div className="h-dvh bg-black p-2 sm:p-4 lg:p-7">
      {/* Bezel. */}
      <div className="bevel h-full border-[6px] p-1 shadow-[0_0_0_2px_#000] sm:p-1.5">
        {/* Glass. */}
        <div className="bevel-in relative h-full overflow-hidden">
          <div className="pix-scroll relative h-full overflow-y-auto">
            {children}
          </div>

          {/* --- CRT overlays, all decorative --- */}
          <div
            aria-hidden="true"
            className="crt-lines pointer-events-none absolute inset-0 z-20 opacity-60"
          />
          <div
            aria-hidden="true"
            className="crt-vignette pointer-events-none absolute inset-0 z-20"
          />
          <div
            aria-hidden="true"
            className="anim-crt-roll pointer-events-none absolute inset-x-0 top-0 z-20 h-16 bg-bone/5"
          />
        </div>
      </div>
    </div>
  );
}

/** Status bar along the top of the glass. Fare counter, not a score. */
function Hud({
  count,
  max,
  ended,
}: {
  count: number;
  max: number;
  ended: boolean;
}) {
  const pad = (n: number) => String(n).padStart(2, "0");

  return (
    <div className="flex shrink-0 items-center justify-between gap-2 border-b-4 border-cab-hi bg-night px-2 py-2 font-pixel text-[7px] sm:px-3 sm:text-[10px]">
      <span className="flex items-center gap-1.5 text-taxi sm:gap-2.5">
        <span className="bevel-gold px-1.5 py-1">TAXI</span>
        <span className="hidden text-bone sm:inline">ABU FADI</span>
      </span>

      <span className="flex items-center gap-2 sm:gap-4">
        {/* A row of pips is readable at a glance in a way "7/12" is not. */}
        <span aria-hidden="true" className="hidden gap-[3px] sm:flex">
          {Array.from({ length: max }, (_, i) => (
            <span
              key={i}
              className={`h-2.5 w-1.5 ${i < count ? "bg-taxi" : "bg-cab-hi"}`}
            />
          ))}
        </span>
        <span className={ended ? "text-blood" : "text-dust"}>
          {ended ? "RIDE OVER" : `TURN ${pad(count)}/${pad(max)}`}
        </span>
      </span>
    </div>
  );
}

function RideOver() {
  // Phase 8 turns this into the reveal.
  return (
    <div className="bevel-gold anim-rise px-3 py-3 text-center">
      <p className="font-pixel text-[10px] sm:text-sm">WSELNA.</p>
      <p className="mt-2 font-term text-lg leading-tight">
        The door is open. The ride is over.
      </p>
    </div>
  );
}
