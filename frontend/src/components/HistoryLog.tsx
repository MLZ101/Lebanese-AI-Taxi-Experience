import { useEffect, useRef } from "react";

import type { Turn } from "../types";

/** Everything said so far, oldest first. The current question lives above. */

interface Props {
  history: Turn[];
}

export function HistoryLog({ history }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [history.length]);

  // The last entry is the question already shown in the panel above.
  const earlier = history.slice(0, -1);
  if (earlier.length === 0) return null;

  return (
    <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1 text-sm">
      {earlier.map((turn, i) => (
        <div
          key={i}
          className={
            turn.role === "passenger"
              ? "ml-8 rounded-lg bg-zinc-800/60 px-3 py-2 text-zinc-300"
              : "mr-8 rounded-lg bg-amber-950/30 px-3 py-2 text-amber-100/70"
          }
        >
          <span className="mr-2 text-[10px] tracking-wider text-zinc-500 uppercase">
            {turn.role === "passenger" ? "you" : "abu fadi"}
          </span>
          {turn.text}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
