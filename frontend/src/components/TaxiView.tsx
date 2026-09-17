import {
  motion,
  type TargetAndTransition,
  type Transition,
} from "framer-motion";

import abuFadi from "../assets/abu-fadi.jpeg";
import type { DriverAction, Mood } from "../types";

/**
 * The back seat of the taxi.
 *
 * There is one piece of art, so Abu Fadi's four reactions are built from
 * camera moves over it rather than separate frames: lean toward the mirror,
 * a slow nod, a greedy flare. Swap in real frames later and only
 * ACTION_MOTION needs to change.
 *
 * The image itself is never animated into view - motion only ever transforms
 * something already on screen, so a dead animation layer costs a reaction,
 * not the scene.
 */

const ACTION_MOTION: Record<DriverAction, TargetAndTransition> = {
  // Just driving.
  normal: { scale: 1, y: 0, filter: "brightness(1) saturate(1)" },
  // Leaning in to study you in the rear-view.
  mirror: { scale: 1.09, y: -4, filter: "brightness(1.08) saturate(1.05)" },
  // Slow, knowing agreement.
  nod: {
    scale: 1.02,
    y: [0, 7, 0, 5, 0],
    filter: "brightness(1.02) saturate(1)",
  },
  // He can smell money.
  money: { scale: 1.06, y: -2, filter: "brightness(1.22) saturate(1.45)" },
};

/*
 * Stepped timings, so a reaction lands in a handful of frames like a sprite
 * animation rather than gliding the way a modern UI would.
 */
const ACTION_TRANSITION: Record<DriverAction, Transition> = {
  normal: { duration: 0.35, ease: "linear" },
  mirror: { duration: 0.25, ease: "linear" },
  nod: { duration: 1.2, ease: "linear" },
  money: { duration: 0.2, ease: "linear" },
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
  action: DriverAction;
  /** Changes every turn, so a reaction replays even if it repeats. */
  turn: number;
}

export function TaxiView({ mood, action, turn }: Props) {
  return (
    <div className="relative aspect-[1024/682] max-h-[32vh] w-full shrink-0 overflow-hidden bg-black sm:max-h-[42vh] lg:max-h-[52vh]">
      {/* Idle engine vibration, always running. */}
      <div className="anim-idle absolute inset-0">
        <motion.img
          key={`${action}-${turn}`}
          src={abuFadi}
          alt="Abu Fadi driving, seen from the back seat"
          initial={false}
          animate={ACTION_MOTION[action]}
          transition={ACTION_TRANSITION[action]}
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

      {action === "money" && <Kaching key={turn} />}
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
