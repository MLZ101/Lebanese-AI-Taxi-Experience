import { useEffect, useRef } from "react";

import type { Radar } from "../types";
import { DASH_ICON } from "./dashIcons";
import { PixelIcon } from "./PixelIcon";

/**
 * ABU FADI'S RADAR.
 *
 * Four things are being measured, presented as the instrument cluster of an
 * early-2000s car: moulded plastic, a strip of fake brushed aluminium, and
 * four round dials with chrome rings, scale ticks, a red zone at the top of
 * each scale, amber backlighting and a needle with mass - it overshoots the
 * reading and settles back, the way a real one does.
 *
 * No numbers anywhere - the player never sees a value. Each dial does carry an
 * etched pictogram and one engraved word, because the icons alone could not
 * separate "how rich he thinks you are" from "what he expects to be handed at
 * the end". Icon, needle arc and word share a colour so the pairing is
 * obvious; the grids live in dashIcons.ts.
 *
 * The cluster also fades up over the ride: barely lit when you get in, hard to
 * ignore by the end, like dash lights coming up as it gets dark.
 */

/** The scale runs over 240 degrees, starting at the lower left. */
const SWEEP = 240;
const START = -120;
const TICKS = 11;

/*
 * Each dial gets one engraved word, the way a real cluster labels FUEL and
 * TEMP. The icon, the needle arc and the word all share a colour, so which
 * gauge is which lands in one glance.
 */
const GAUGES = [
  { key: "money", label: "MONEY", arc: "#f2c230", ink: "text-taxi" },
  { key: "status", label: "STATUS", arc: "#7d96a8", ink: "text-sky" },
  // Orange, not red - the red zone at the top of every scale is already red.
  { key: "suspicion", label: "DOUBT", arc: "#e0701f", ink: "text-rust" },
  { key: "tip", label: "TIP", arc: "#2f7d3a", ink: "text-cedar" },
] as const;

interface Props {
  radar: Radar;
  /** Drives how prominent the cluster is. It creeps up on you. */
  messageCount: number;
}

export function RadarPanel({ radar, messageCount }: Props) {
  // Last rendered values, so a dial can react to having just moved.
  const previous = useRef<Radar | null>(null);
  const before = previous.current;
  useEffect(() => {
    previous.current = radar;
  });

  // Dim at the start of the ride, fully lit by the end.
  const presence = Math.min(1, messageCount / 6);

  return (
    <div
      className="bevel dash-plastic shrink-0 transition-opacity duration-1000"
      style={{ opacity: 0.5 + 0.5 * presence }}
    >
      {/* The silver trim strip, with the aftermarket brand plate on it. */}
      <div className="dash-trim flex items-center justify-between gap-2 px-2 py-1.5">
        <span className="dash-engraved font-pixel text-[9px] tracking-wider sm:text-[12px]">
          ABU FADI'S RADAR
        </span>
        {/* Two moulded screw heads, because it was fitted by a cousin. */}
        <span aria-hidden="true" className="flex shrink-0 gap-1.5">
          <span className="h-2 w-2 bg-black/40" />
          <span className="h-2 w-2 bg-black/40" />
        </span>
      </div>

      {/* Always one row: stacking these 2x2 on a phone pushes the dialogue
          box and the input off the bottom of the screen. */}
      <div className="grid grid-cols-4 gap-1.5 p-2 sm:gap-2">
        {GAUGES.map(({ key, label, arc, ink }) => (
          <Dial
            key={key}
            icon={DASH_ICON[key]}
            label={label}
            arc={arc}
            ink={ink}
            value={radar[key]}
            moved={before !== null && before[key] !== radar[key]}
          />
        ))}
      </div>

      {/* Vent slots along the bottom, so the panel sits in a dashboard. */}
      <div aria-hidden="true" className="flex gap-1 px-2 pb-2">
        {Array.from({ length: 22 }, (_, i) => (
          <span key={i} className="h-1 flex-1 bg-black/60" />
        ))}
      </div>
    </div>
  );
}

/** Polar helper - degrees clockwise from twelve o'clock, on a 100x100 face. */
function point(angle: number, radius: number) {
  const rad = ((angle - 90) * Math.PI) / 180;
  return {
    x: 50 + radius * Math.cos(rad),
    y: 50 + radius * Math.sin(rad),
  };
}

/** The full 240-degree scale, as one path the progress arc can be dashed over. */
function scalePath(radius: number) {
  const from = point(START, radius);
  const to = point(START + SWEEP, radius);
  return `M ${from.x} ${from.y} A ${radius} ${radius} 0 1 1 ${to.x} ${to.y}`;
}

function Dial({
  icon,
  label,
  arc,
  ink,
  value,
  moved,
}: {
  icon: string;
  label: string;
  arc: string;
  ink: string;
  value: number;
  moved: boolean;
}) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className={moved ? "anim-meter-flash" : undefined}>
      <div className="dial relative">
        {/* The bulb behind the face. */}
        <div
          aria-hidden="true"
          className="dial-glow pointer-events-none absolute inset-0"
        />

        <svg viewBox="0 0 100 100" className="relative block w-full">
          {/* Chrome ring, then the well it sits in, then the face. */}
          <circle cx="50" cy="50" r="49" fill="#0a0a08" />
          <circle
            cx="50"
            cy="50"
            r="47"
            fill="none"
            stroke="#8f8f86"
            strokeWidth="2"
          />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="#2b2b22"
            strokeWidth="3"
          />
          <circle cx="50" cy="50" r="42" fill="#0d0d10" />
  
          {/* Scale ticks, longer at each end of the run. */}
          {Array.from({ length: TICKS }, (_, i) => {
            const angle = START + (i * SWEEP) / (TICKS - 1);
            const long = i === 0 || i === TICKS - 1;
            const a = point(angle, long ? 30 : 33);
            const b = point(angle, 38);
            return (
              <line
                key={i}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke="#e8e2cf"
                strokeOpacity={long ? 0.75 : 0.4}
                strokeWidth={long ? 3 : 2}
              />
            );
          })}
  
          {/* The red zone at the top of the scale. Every car has one. */}
          <path
            d={scalePath(40)}
            fill="none"
            stroke="#b02a1f"
            strokeWidth="3"
            pathLength="100"
            strokeDasharray="20 100"
            strokeDashoffset="-80"
          />
  
          {/* The reading itself, dashed over the scale path. */}
          <path
            d={scalePath(40)}
            fill="none"
            stroke={arc}
            strokeWidth="3"
            pathLength="100"
            strokeDasharray={`${clamped} 100`}
            style={{ transition: "stroke-dasharray 700ms ease-out" }}
          />
  
          {/* Needle and hub cap. */}
          <g
            className="dial-needle"
            style={{ transform: `rotate(${START + (clamped / 100) * SWEEP}deg)` }}
          >
            <polygon points="47.5,52 50,14 52.5,52" fill="#f4f1e4" />
            <polygon points="48.5,52 50,14 50,52" fill="#b9b5a5" />
          </g>
          <circle cx="50" cy="50" r="5" fill="#6f6f68" />
          <circle cx="50" cy="50" r="3" fill="#1a1a14" />
        </svg>

        {/*
         * The pictogram, etched into the lower half of the face. 36px for a
         * 9x9 grid is exactly 4px a cell, so nothing blurs.
         */}
        <div
          className={`pointer-events-none absolute inset-x-0 bottom-[13%] flex justify-center ${ink}`}
        >
          {/* 27px then 36px - both whole multiples of the 9x9 grid. */}
          <PixelIcon grid={icon} className="h-[27px] w-[27px] sm:h-9 sm:w-9" />
        </div>
      </div>

      {/* The word, moulded into the plastic under the dial. */}
      <p
        className={`dash-label mt-0.5 text-center font-pixel text-[8px] tracking-wider sm:text-[9px] ${ink}`}
      >
        {label}
      </p>
    </div>
  );
}
