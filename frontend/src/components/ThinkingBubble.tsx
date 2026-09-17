import type { Mood } from "../types";

/** Abu Fadi muttering to himself. Not reasoning - just a reaction. */

const MOOD_STYLE: Record<Mood, string> = {
  neutral: "border-zinc-700 text-zinc-400",
  curious: "border-amber-700/60 text-amber-300",
  suspicious: "border-orange-800/70 text-orange-300",
  excited: "border-yellow-500/70 text-yellow-300",
  upset: "border-red-800/70 text-red-300",
};

interface Props {
  thinking: string;
  mood: Mood;
  waiting: boolean;
}

export function ThinkingBubble({ thinking, mood, waiting }: Props) {
  if (!waiting && !thinking) return <div className="h-9" />;

  return (
    <div className="h-9">
      <div
        key={waiting ? "dots" : thinking}
        className={`anim-fade inline-flex items-center gap-2 rounded-full border bg-black/40 px-4 py-1.5 font-mono text-sm italic ${MOOD_STYLE[mood]}`}
      >
        {waiting ? <Dots /> : thinking}
      </div>
    </div>
  );
}

function Dots() {
  return (
    <span className="flex gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="anim-blink h-1.5 w-1.5 rounded-full bg-current"
          style={{ animationDelay: `${i * 0.18}s` }}
        />
      ))}
    </span>
  );
}
