import { useEffect, useRef } from "react";

import type { Turn } from "../types";

/**
 * Everything said so far, oldest first. The current question lives above.
 *
 * Presented as a scrolling transcript window rather than chat bubbles -
 * speaker tags in the left margin, no rounded anything.
 */

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

  // Turn one: show the empty log rather than a hole, so the column has the
  // same shape it will have for the rest of the ride.
  if (earlier.length === 0) {
    return (
      <div className="bevel-in hidden min-h-0 flex-1 overflow-hidden lg:block">
        <Title />
        <p className="p-2 font-term text-lg text-khaki">
          Nothing said yet. The meter is not running.
        </p>
      </div>
    );
  }

  return (
    <div className="bevel-in min-h-0 flex-1 overflow-hidden">
      <Title />

      <div className="pix-scroll max-h-40 min-h-0 space-y-1.5 overflow-y-auto p-2 lg:max-h-none">
        {earlier.map((turn, i) => {
          const you = turn.role === "passenger";
          return (
            <p key={i} className="font-term text-lg leading-tight">
              <span
                className={`mr-2 font-pixel text-[7px] ${
                  you ? "text-sky" : "text-taxi"
                }`}
              >
                {you ? "YOU" : "HIM"}
              </span>
              <span className={you ? "text-dust" : "text-bone"}>
                {turn.text}
              </span>
            </p>
          );
        })}
        <div ref={endRef} />
      </div>
    </div>
  );
}

/** The log window's header bar. */
function Title() {
  return (
    <p className="border-b-4 border-cab-hi px-2 py-1 font-pixel text-[6px] text-khaki sm:text-[8px]">
      ── TRANSCRIPT ──
    </p>
  );
}
