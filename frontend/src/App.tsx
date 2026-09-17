import { AnswerInput } from "./components/AnswerInput";
import { HistoryLog } from "./components/HistoryLog";
import { QuestionPanel } from "./components/QuestionPanel";
import { ThinkingBubble } from "./components/ThinkingBubble";
import { useGame } from "./hooks/useGame";

export default function App() {
  const { state, phase, error, waiting, canAnswer, start, answer } = useGame();

  // No state yet means the ride never started - including when start failed,
  // so the player can try again instead of staring at a locked screen.
  if (!state) {
    return (
      <TitleScreen
        onStart={start}
        starting={phase === "starting"}
        error={error}
      />
    );
  }

  return (
    <div className="flex h-dvh flex-col bg-zinc-950 text-zinc-100 lg:flex-row">
      {/* Left: the taxi itself. Built in phase 5. */}
      <section className="flex min-h-[30vh] flex-1 items-center justify-center border-b border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 lg:border-r lg:border-b-0">
        <p className="px-6 text-center text-xs tracking-[0.3em] text-zinc-700 uppercase">
          taxi view
        </p>
      </section>

      {/* Right: the conversation. */}
      <section className="flex min-h-0 w-full flex-col gap-4 p-5 sm:p-8 lg:max-w-xl">
        <Header count={state.message_count} max={state.max_messages} />

        <HistoryLog history={state.history} />

        <div className="space-y-4">
          <ThinkingBubble
            thinking={state.thinking}
            mood={state.mood}
            waiting={waiting}
          />
          <QuestionPanel
            question={state.question}
            turn={state.message_count}
            dimmed={waiting}
          />

          {error && (
            <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
              {error}
            </p>
          )}

          {state.game_status === "ended" ? (
            <RideOver />
          ) : (
            <AnswerInput
              disabled={!canAnswer}
              waiting={waiting}
              onSubmit={answer}
            />
          )}

          {state.ai_degraded && (
            <p className="text-xs text-zinc-600">
              The radio cut out for a second - Abu Fadi kept talking anyway.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

function Header({ count, max }: { count: number; max: number }) {
  return (
    <div className="flex items-baseline justify-between">
      <h1 className="text-xs tracking-[0.25em] text-amber-600/80 uppercase">
        Abu Fadi
      </h1>
      <span className="font-mono text-xs text-zinc-700">
        {count}/{max}
      </span>
    </div>
  );
}

function RideOver() {
  // Phase 8 turns this into the reveal.
  return (
    <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 px-4 py-3 text-sm text-amber-200/80">
      Wselna. The ride is over.
    </div>
  );
}

function TitleScreen({
  onStart,
  starting,
  error,
}: {
  onStart: () => void;
  starting: boolean;
  error: string | null;
}) {
  return (
    <div className="flex h-dvh flex-col items-center justify-center gap-8 bg-zinc-950 px-6 text-center">
      <div className="anim-rise space-y-3">
        <p className="text-xs tracking-[0.4em] text-zinc-600 uppercase">
          Beirut, sometime after 6pm
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-amber-400 sm:text-5xl">
          THE LEBANESE
          <br />
          TAXI EXPERIENCE
        </h1>
        <p className="text-sm text-zinc-500">A taxi stops. You get in.</p>
      </div>

      <button
        className="anim-fade-late rounded-lg bg-amber-500 px-8 py-3 font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-60"
        type="button"
        onClick={onStart}
        disabled={starting}
      >
        {starting ? "Getting in..." : error ? "Try again" : "Get in"}
      </button>

      {error && (
        <p className="max-w-sm text-sm text-red-400/80">{error}</p>
      )}
    </div>
  );
}
