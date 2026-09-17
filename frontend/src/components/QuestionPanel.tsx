/**
 * Exactly one question on screen at a time, in a console dialogue box.
 *
 * The nameplate sits on the top border the way every 90s RPG did it, and a
 * blinking arrow in the corner says the box is waiting on you.
 *
 * The box holds its height while `ready` is false - he is still thinking in
 * the panel above - so nothing below it jumps when the question lands.
 *
 * The `turn` key remounts the paragraph, which replays the CSS entry
 * animation. No JS animation library in the path - if anything breaks, the
 * question is still readable.
 */

interface Props {
  question: string;
  /** Remounts the element so the entry animation replays each turn. */
  turn: number;
  /**
   * False only while a new thought is still typing itself out. While the
   * request is merely in flight this stays true, so the question he asked
   * last turn is still on screen rather than blinking out.
   */
  ready: boolean;
  /** He is working - fade what is already there instead of hiding it. */
  dimmed: boolean;
}

export function QuestionPanel({ question, turn, ready, dimmed }: Props) {
  return (
    <div className="relative mt-3.5">
      {/* Nameplate, straddling the top edge of the box. */}
      <span className="bevel-gold absolute -top-2.5 left-3 z-10 px-2 py-1 font-pixel text-[7px] sm:text-[9px]">
        ABU FADI
      </span>

      <div className="bevel-in min-h-[7rem] px-3 pt-5 pb-7 sm:min-h-[8rem] sm:px-4">
        {ready && (
          <p
            key={turn}
            className={`anim-rise font-term text-xl leading-tight text-bone transition-opacity duration-200 sm:text-3xl ${
              dimmed ? "opacity-40" : "opacity-100"
            }`}
          >
            {question}
          </p>
        )}

        {/* Your move. Only once it is actually your move. */}
        {ready && !dimmed && (
          <span
            aria-hidden="true"
            className="anim-nudge absolute right-3 bottom-2 font-pixel text-[9px] text-taxi"
          >
            ▼
          </span>
        )}
      </div>
    </div>
  );
}
