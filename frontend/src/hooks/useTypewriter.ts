import { useEffect, useState } from "react";

/**
 * Reveals a string one character at a time.
 *
 * The backend hands us the whole turn at once, so there is nothing genuinely
 * streaming here - this replays it as if there were, which is what makes Abu
 * Fadi look like he is working the thought out rather than having had it
 * ready.
 *
 * `turn` restarts the run even when the text is identical to last time, which
 * happens often - he mutters the same short things a lot.
 */
export function useTypewriter(text: string, turn: number, speed = 24) {
  /*
   * Progress is stored against the turn it belongs to, so a new turn reads as
   * "nothing revealed yet" during render. Resetting in an effect instead would
   * mean a second render pass every turn.
   */
  const [progress, setProgress] = useState<{ turn: number; n: number }>({
    turn: Number.NaN,
    n: 0,
  });

  // Read once: the whole point is that this does not change mid-ride.
  const [reduced] = useState(
    () =>
      typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  const revealed = progress.turn === turn ? progress.n : 0;

  useEffect(() => {
    if (reduced || !text) return;

    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setProgress({ turn, n: i });
      if (i >= text.length) clearInterval(id);
    }, speed);

    /*
     * The question and the answer box are both gated on this finishing, so a
     * timer that never lands would soft-lock the ride. Force completion well
     * after it should have ended rather than risk that.
     */
    const guard = setTimeout(
      () => {
        clearInterval(id);
        setProgress({ turn, n: text.length });
      },
      text.length * speed + 2000,
    );

    return () => {
      clearInterval(id);
      clearTimeout(guard);
    };
  }, [text, turn, speed, reduced]);

  const shown = reduced ? text : text.slice(0, revealed);

  return { shown, done: shown.length >= text.length };
}
