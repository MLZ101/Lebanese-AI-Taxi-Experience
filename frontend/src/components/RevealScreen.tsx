import { useState } from "react";

import type { Verdict } from "../types";
import { CreditsPanel } from "./CreditsPanel";

/**
 * The payoff.
 *
 * Everything the ride was quietly doing gets named here: the innocent questions
 * were a guessing game, the dials were a scoreboard, and Abu Fadi has a call to
 * make. It stays a *guess* - the player says whether he got it, and he has a
 * line ready either way. He does not take being wrong well.
 *
 * Laid out as the game-over card of a cabinet: a results plate, then the
 * scorecard underneath.
 */

interface Props {
  verdict: Verdict;
  turns: number;
  onRideAgain: () => void;
}

export function RevealScreen({ verdict, turns, onRideAgain }: Props) {
  const [answered, setAnswered] = useState<"right" | "wrong" | null>(null);

  return (
    <div className="anim-rise space-y-3">
      <header className="bevel-gold px-3 py-2.5 text-center">
        <p className="font-pixel text-[6px] tracking-[0.25em] sm:text-[8px]">
          {String(turns).padStart(2, "0")} QUESTIONS LATER
        </p>
        <p className="mt-2 font-pixel text-[10px] leading-relaxed sm:text-sm">
          ABU FADI HAS
          <br />
          REACHED A CONCLUSION
        </p>
      </header>

      <p className="bevel-in px-3 py-2 font-term text-lg leading-tight text-bone">
        The whole ride he was playing his own game in his head. He calls it{" "}
        <span className="text-taxi">Tawa2ef Guesser</span>. He never asked you
        once. He has been keeping score.
      </p>

      {/* The call itself. */}
      <section className="bevel px-3 py-3">
        <p className="font-pixel text-[6px] tracking-[0.25em] text-taxi-dk sm:text-[8px]">
          HIS GUESS
        </p>
        <p className="mt-2 font-term text-2xl leading-tight text-taxi sm:text-3xl">
          {verdict.guess}
        </p>

        {answered === null ? (
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              onClick={() => setAnswered("right")}
              className="bevel-gold flex-1 px-3 py-2.5 font-pixel text-[8px] hover:bg-taxi-hi sm:text-[10px]"
            >
              ▶ SA7 — HE GOT IT
            </button>
            <button
              type="button"
              onClick={() => setAnswered("wrong")}
              className="bevel flex-1 px-3 py-2.5 font-pixel text-[8px] text-bone hover:bg-cab-hi sm:text-[10px]"
            >
              ▶ GHALAT — WRONG
            </button>
          </div>
        ) : (
          <p className="bevel-in anim-rise mt-3 px-3 py-2 font-term text-xl leading-tight text-bone">
            {answered === "right" ? verdict.if_right : verdict.if_wrong}
          </p>
        )}
      </section>

      <Finding label="ON YOUR MONEY" text={verdict.money_verdict} />
      <Finding label="AND THE REST OF YOU" text={verdict.background_verdict} />

      {verdict.evidence.length > 0 && (
        <section className="bevel-in px-3 py-2">
          <p className="font-pixel text-[6px] tracking-[0.25em] text-taxi-dk sm:text-[8px]">
            HIS EVIDENCE (ALL OF IT NONSENSE)
          </p>
          <ul className="mt-2 space-y-1">
            {verdict.evidence.map((item, i) => (
              <li
                key={i}
                className="flex gap-2 font-term text-lg leading-tight text-dust"
              >
                <span className="text-taxi-dk">◈</span>
                {item}
              </li>
            ))}
          </ul>
        </section>
      )}

      {verdict.fare && (
        <p className="px-1 font-term text-lg leading-tight text-khaki">
          {verdict.fare}
        </p>
      )}

      {verdict.closing_line && (
        <p className="px-1 font-term text-xl leading-tight text-bone">
          &ldquo;{verdict.closing_line}&rdquo;
        </p>
      )}

      <button
        type="button"
        onClick={onRideAgain}
        className="bevel-gold w-full px-4 py-3 font-pixel text-[9px] tracking-wider hover:bg-taxi-hi sm:text-[11px]"
      >
        ▶ TAKE ANOTHER TAXI
      </button>

      {/* Credits last, the way the cabinet would roll them. */}
      <CreditsPanel />
    </div>
  );
}

function Finding({ label, text }: { label: string; text: string }) {
  return (
    <section className="px-1">
      <p className="font-pixel text-[6px] tracking-[0.25em] text-taxi-dk sm:text-[8px]">
        {label}
      </p>
      <p className="mt-1.5 font-term text-xl leading-tight text-bone">{text}</p>
    </section>
  );
}
