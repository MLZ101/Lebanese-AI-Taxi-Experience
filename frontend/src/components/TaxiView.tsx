import { useEffect, useRef, useState } from "react";
import {
  motion,
  type TargetAndTransition,
  type Transition,
} from "framer-motion";

import abuFadi from "../assets/abu-fadi.jpeg";
import greedClip from "../assets/excited-money.mp4";
import doubtClip from "../assets/upset-suspicious.mp4";
import type { Mood } from "../types";

/**
 * The back seat of the taxi.
 *
 * Mood is the only reaction signal - it drives the colour of the cabin, what
 * Abu Fadi's body does, and which clip comes up. Two layers do the work.
 *
 * **Underneath, the painting**, always mounted. There is one piece of art, so
 * the five moods are camera moves over it rather than separate frames: a
 * glance at the mirror, turning to study you, a greedy flare. Swap in real
 * frames later and only MOOD_MOTION needs to change.
 *
 * **On top, two reaction clips.** A mood that lands him somewhere strong plays
 * one, once, and the painting comes back when it ends. Neutral turns never
 * leave the painting.
 *
 * Nothing here is load-bearing: if a clip stalls, errors, or autoplay is
 * refused, the painting is already underneath and the scene carries on. The
 * image is never animated *into* view for the same reason - motion only ever
 * transforms something already on screen.
 */

/** Which clip a mood pulls up, if any. Neutral stays on the painting. */
const MOOD_CLIP: Partial<Record<Mood, "greed" | "doubt">> = {
  excited: "greed",
  curious: "greed",
  suspicious: "doubt",
  upset: "doubt",
};

const CLIP_SRC = {
  greed: greedClip,
  doubt: doubtClip,
} as const;

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
  const clip = MOOD_CLIP[mood];

  /*
   * The turn whose clip has already finished. Derived rather than stored the
   * other way round: a new turn is automatically "not finished yet", so the
   * clip replays even when the mood is the same two turns running.
   */
  const [spentTurn, setSpentTurn] = useState<number | null>(null);
  const playing = Boolean(clip) && spentTurn !== turn;

  const greedRef = useRef<HTMLVideoElement>(null);
  const doubtRef = useRef<HTMLVideoElement>(null);

  // Both clips stay mounted and preloaded, so starting one is instant - a
  // fresh <video> every turn would stall on the first frame.
  useEffect(() => {
    if (!clip || !playing) return;

    const el = (clip === "greed" ? greedRef : doubtRef).current;
    if (!el) return;

    el.currentTime = 0;
    const started = el.play();
    // Autoplay refused, codec trouble, anything: fall straight back to the
    // painting rather than sitting on a frozen frame.
    if (started) started.catch(() => setSpentTurn(turn));
  }, [clip, playing, turn]);

  /** Both ends of a switch - clip in, clip out - get the same flourish. */
  const done = () => setSpentTurn(turn);

  /*
   * The picture squashing back out of a scanline has to run on the layer
   * holding the clips, and that layer must never remount or the preloaded
   * videos would be thrown away. So this one flourish is driven imperatively
   * instead of by a CSS class on a keyed element, like the rest of them.
   */
  const stageRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const stage = stageRef.current;
    if (!stage || typeof stage.animate !== "function") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    stage.animate(
      [
        { transform: "scaleY(0.4) scaleX(1.02)", filter: "brightness(2.4)" },
        {
          transform: "scaleY(1.03) scaleX(1)",
          filter: "brightness(1.15)",
          offset: 0.55,
        },
        { transform: "none", filter: "none" },
      ],
      { duration: 420, easing: "steps(7, end)" },
    );
  }, [turn, playing]);

  return (
    <div className="relative aspect-[1024/682] max-h-[32vh] w-full shrink-0 overflow-hidden bg-black sm:max-h-[42vh] lg:max-h-[52vh]">
      {/* Idle engine vibration, always running, under everything. */}
      <div ref={stageRef} className="anim-idle absolute inset-0">
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

        {/*
         * The clips are 16:9 against the painting's 3:2, so object-cover
         * crops them to the same window instead of letterboxing - the cabin
         * keeps its shape and only the framing shifts.
         */}
        {(["greed", "doubt"] as const).map((name) => (
          <video
            key={name}
            ref={name === "greed" ? greedRef : doubtRef}
            src={CLIP_SRC[name]}
            muted
            playsInline
            preload="auto"
            aria-hidden="true"
            onEnded={done}
            onError={done}
            className={`pointer-events-none absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${
              playing && clip === name ? "opacity-100" : "opacity-0"
            }`}
          />
        ))}
      </div>

      {/* Mood wash, over whichever layer is showing. */}
      <div
        className={`pointer-events-none absolute inset-0 transition-colors duration-700 ${MOOD_WASH[mood]}`}
      />

      {/* A streetlight sweeping past the windscreen. */}
      <div className="anim-sweep pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 bg-taxi-hi/10" />

      {/*
       * Scanlines and vignette sit above both layers, which is most of why a
       * photographic clip and a painting read as the same scene at all.
       */}
      <div
        aria-hidden="true"
        className="crt-lines pointer-events-none absolute inset-0 opacity-40"
      />
      <div
        aria-hidden="true"
        className="crt-vignette pointer-events-none absolute inset-0"
      />

      {/* Remounting on every switch replays the channel change. */}
      <ChannelChange key={`${turn}-${playing ? clip : "still"}`} />

      {mood === "excited" && <Kaching key={turn} />}
    </div>
  );
}

/**
 * The cabinet changing channel: the tube flares, a tracking bar rolls down
 * the glass, and the picture reopens from a scanline. Purely decorative - it
 * covers the seam between two different aspect ratios.
 */
function ChannelChange() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-0">
      <div className="anim-channel-flare absolute inset-0 bg-taxi-hi/70" />
      <div className="anim-channel-roll absolute inset-x-0 top-0 h-1/4 bg-gradient-to-b from-transparent via-bone/25 to-transparent" />
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
