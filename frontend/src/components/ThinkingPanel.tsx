import type { Mood } from "../types";

/**
 * What Abu Fadi is thinking, typing itself out.
 *
 * Deliberately given the same weight as the thing he actually says: its own
 * panel, above the dialogue box, in the reading order an AI chat puts thinking
 * in. Dashed border where the speech box is solid, and the whole panel takes
 * the colour of his mood, so a turn that makes him suspicious looks different
 * across the room.
 *
 * It is not real streaming - the backend sends the whole turn at once and
 * useTypewriter replays it. See that hook.
 */

const MOOD_INK: Record<Mood, string> = {
  neutral: "text-dust",
  curious: "text-taxi",
  suspicious: "text-sky",
  excited: "text-taxi-hi",
  upset: "text-rust",
};

const MOOD_TAG: Record<Mood, string> = {
  neutral: "HMM",
  curious: "CURIOUS",
  suspicious: "SUSPICIOUS",
  excited: "EXCITED",
  upset: "UPSET",
};

interface Props {
  /** The text revealed so far, from useTypewriter. */
  shown: string;
  /** False while more characters are still arriving. */
  done: boolean;
  mood: Mood;
  /** True while the request is still in flight - nothing to show yet. */
  waiting: boolean;
}

export function ThinkingPanel({ shown, done, mood, waiting }: Props) {
  // Mood colours the text, the caret and the dashed border alike.
  const ink = MOOD_INK[mood];

  return (
    <div className={`relative mt-2.5 ${ink}`}>
      {/* Nameplate, straddling the top edge like the dialogue box's. */}
      <span className="bevel absolute -top-2.5 left-3 z-10 px-2 py-1 font-pixel text-[7px] sm:text-[9px]">
        {waiting ? "THINKING" : `THINKING — ${MOOD_TAG[mood]}`}
      </span>

      <div className="thought-box min-h-[4.25rem] px-3 pt-5 pb-3 sm:min-h-[5rem] sm:px-4">
        {/* Same size as what he says out loud - italics and the dashed
            border carry the difference, not a smaller font. */}
        <p className="font-term text-xl leading-tight italic sm:text-3xl">
          {waiting ? (
            <Dots />
          ) : (
            <>
              {shown}
              {/* The caret only exists while characters are still landing. */}
              {!done && <span className="anim-blink caret ml-[2px]" />}
            </>
          )}
        </p>
      </div>
    </div>
  );
}

/** Square dots - round ones would give the era away. */
function Dots() {
  return (
    <span className="flex items-center gap-1.5 py-1.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="anim-blink-soft h-2 w-2 bg-current"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </span>
  );
}
