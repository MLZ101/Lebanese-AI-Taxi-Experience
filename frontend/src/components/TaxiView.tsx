import {
  motion,
  type TargetAndTransition,
  type Transition,
} from "framer-motion";

import abuFadi from "../assets/abu-fadi.jpeg";
import type { Mood } from "../types";

/**
 * The back seat of the taxi.
 *
 * Mood is the only reaction signal - it drives both the colour of the cabin
 * and what Abu Fadi's body does. There is one piece of art, so the five moods
 * are camera moves over it rather than separate frames: a glance at the
 * mirror, turning to study you, a greedy flare. Swap in real frames later and
 * only MOOD_MOTION needs to change.
 *
 * The image itself is never animated into view - motion only ever transforms
 * something already on screen, so a dead animation layer costs a reaction,
 * not the scene.
 */

const MOOD_MOTION: Record<Mood, TargetAndTransition> = {
  // Just driving.
  neutral: { scale: 1, y: 0, filter: "brightness(1) saturate(1)" },
  // A glance up at the mirror.
  curious: { scale: 1.05, y: -3, filter: "brightness(1.05) saturate(1.05)" },
  // Turning to properly study you.
  suspicious: { scale: 1.12, y: -5, filter: "brightness(0.92) saturate(0.85)" },
  // He can smell money.
  excited: { scale: 1.08, y: -2, filter: "brightness(1.22) saturate(1.45)" },
  // Slow, disappointed nod.
  upset: {
    scale: 1.02,
    y: [0, 8, 0, 5, 0],
    filter: "brightness(0.85) saturate(0.9)",
  },
};

/*
 * Stepped timings, so a reaction lands in a handful of frames like a sprite
 * animation rather than gliding the way a modern UI would.
 */
const MOOD_TRANSITION: Record<Mood, Transition> = {
  neutral: { duration: 0.35, ease: "linear" },
  curious: { duration: 0.3, ease: "linear" },
  suspicious: { duration: 0.25, ease: "linear" },
  excited: { duration: 0.2, ease: "linear" },
  upset: { duration: 1.2, ease: "linear" },
};

/** A colour wash over the whole cabin. Kept low so the art still reads. */
const MOOD_WASH: Record<Mood, string> = {
  neutral: "bg-transparent",
  curious: "bg-taxi/10",
  suspicious: "bg-sky/20",
  excited: "bg-taxi-hi/15",
  upset: "bg-blood/25",
};

interface Props {
  mood: Mood;
  /** Changes every turn, so a reaction replays even if the mood repeats. */
  turn: number;
}

export function TaxiView({ mood, turn }: Props) {
  return (
    <div className="relative aspect-[1024/682] max-h-[32vh] w-full shrink-0 overflow-hidden bg-black sm:max-h-[42vh] lg:max-h-[52vh]">
      {/* Idle engine vibration, always running. */}
      <div className="anim-idle absolute inset-0">
        <motion.img
          key={`${mood}-${turn}`}
          src={abuFadi}
          alt="Abu Fadi driving, seen from the back seat"
          initial={false}
          animate={MOOD_MOTION[mood]}
          transition={MOOD_TRANSITION[mood]}
          style={{ originX: 0.36, originY: 0.42, imageRendering: "pixelated" }}
          className="h-full w-full object-cover object-[50%_26%]"
        />
      </div>

      {/* Mood wash. */}
      <div
        className={`pointer-events-none absolute inset-0 transition-colors duration-700 ${MOOD_WASH[mood]}`}
      />

      {/* A streetlight sweeping past the windscreen. */}
      <div className="anim-sweep pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 bg-taxi-hi/10" />

      {/* Scanlines on the art too, so it sits in the same tube as the chrome. */}
      <div
        aria-hidden="true"
        className="crt-lines pointer-events-none absolute inset-0 opacity-40"
      />
      <div
        aria-hidden="true"
        className="crt-vignette pointer-events-none absolute inset-0"
      />

      {mood === "excited" && <Kaching key={turn} />}
    </div>
  );
}

/** The KACHING moment. Decorative only. */
function Kaching() {
  return (
    <>
      <div className="anim-kaching pointer-events-none absolute inset-0 bg-taxi/30" />
      <p className="anim-kaching-pop pix-shadow pointer-events-none absolute top-1/2 left-1/2 font-pixel text-base text-taxi-hi sm:text-2xl">
        KA-CHING!
      </p>
    </>
  );
}
