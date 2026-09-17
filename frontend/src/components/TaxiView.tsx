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
  nod: { scale: 1.02, y: [0, 7, 0, 5, 0], filter: "brightness(1.02) saturate(1)" },
  // He can smell money.
  money: { scale: 1.06, y: -2, filter: "brightness(1.22) saturate(1.45)" },
};

const ACTION_TRANSITION: Record<DriverAction, Transition> = {
  normal: { type: "spring", stiffness: 60, damping: 18 },
  mirror: { type: "spring", stiffness: 90, damping: 14 },
  nod: { duration: 1.4, ease: "easeInOut" },
  money: { type: "spring", stiffness: 260, damping: 11 },
};

/** A colour wash over the whole cabin. Kept low so the art still reads. */
const MOOD_WASH: Record<Mood, string> = {
  neutral: "bg-transparent",
  curious: "bg-amber-500/10",
  suspicious: "bg-indigo-900/25",
  excited: "bg-yellow-400/15",
  upset: "bg-red-800/25",
};

interface Props {
  mood: Mood;
  action: DriverAction;
  /** Changes every turn, so a reaction replays even if it repeats. */
  turn: number;
}

export function TaxiView({ mood, action, turn }: Props) {
  return (
    <div className="relative aspect-[1024/682] max-h-[62vh] w-full shrink-0 overflow-hidden bg-black">
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
      <div className="anim-sweep pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 bg-gradient-to-r from-transparent via-amber-200/10 to-transparent" />

      {/* Cabin vignette - keeps the eye on the driver. */}
      <div className="pointer-events-none absolute inset-0 shadow-[inset_0_0_140px_40px_rgba(0,0,0,0.75)]" />

      {action === "money" && <Kaching key={turn} />}
    </div>
  );
}

/** The KACHING moment. Decorative only. */
function Kaching() {
  return (
    <>
      <div className="anim-kaching pointer-events-none absolute inset-0 bg-amber-300/25" />
      <div className="anim-kaching-pop pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-5xl drop-shadow-[0_0_18px_rgba(251,191,36,0.9)]">
        💰
      </div>
    </>
  );
}
