/**
 * Exactly one question on screen at a time.
 *
 * The `turn` key remounts the paragraph, which replays the CSS entry
 * animation. No JS animation library in the path - if anything breaks, the
 * question is still readable.
 */

interface Props {
  question: string;
  /** Remounts the element so the entry animation replays each turn. */
  turn: number;
  dimmed: boolean;
}

export function QuestionPanel({ question, turn, dimmed }: Props) {
  return (
    <div className="min-h-[7rem]">
      <p
        key={turn}
        className={`anim-rise text-2xl leading-snug font-medium text-amber-50 transition-opacity duration-300 sm:text-3xl ${
          dimmed ? "opacity-40" : "opacity-100"
        }`}
      >
        {question}
      </p>
    </div>
  );
}
