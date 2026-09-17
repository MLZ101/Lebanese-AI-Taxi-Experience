import { useEffect, useRef } from "react";

import type { Radar } from "../types";

/**
 * ABU FADI'S RADAR.
 *
 * Four things are being measured and the player is never told what. No
 * labels, no numbers - only glyphs and a row of segments that fills and
 * empties, like something aftermarket wired into the dash years ago.
 *
 * The panel also fades up over the ride: barely lit when you get in, hard to
 * ignore by the end.
 */

const SEGMENTS = 16;

const BARS = [
  { key: "money", glyph: "\u25c8", lit: "bg-amber-400", flash: "shadow-amber-400/70" },
  { key: "status", glyph: "\u2b22", lit: "bg-sky-400", flash: "shadow-sky-400/70" },
  { key: "suspicion", glyph: "\u25c9", lit: "bg-orange-500", flash: "shadow-orange-500/70" },
  { key: "tip", glyph: "\u2726", lit: "bg-emerald-400", flash: "shadow-emerald-400/70" },
] as const;

interface Props {
  radar: Radar;
  /** Drives how prominent the panel is. It creeps up on you. */
  messageCount: number;
}

export function RadarPanel({ radar, messageCount }: Props) {
  // Last rendered values, so a bar can react to having just moved.
  const previous = useRef<Radar | null>(null);
  const before = previous.current;
  useEffect(() => {
    previous.current = radar;
  });

  // Dim at the start of the ride, fully lit by the end.
  const presence = Math.min(1, messageCount / 6);

  return (
    <div
      className="rounded-md border bg-black/70 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] transition-all duration-1000"
      style={{
        opacity: 0.45 + 0.55 * presence,
        borderColor: `rgba(180, 130, 40, ${0.15 + 0.35 * presence})`,
      }}
    >
      <p
        className="mb-2.5 text-[9px] tracking-[0.35em] text-amber-700 uppercase transition-opacity duration-1000"
        style={{ opacity: 0.5 + 0.5 * presence }}
      >
        Abu Fadi's Radar
      </p>

      <div className="space-y-1.5">
        {BARS.map(({ key, glyph, lit, flash }) => (
          <Meter
            key={key}
            glyph={glyph}
            lit={lit}
            flash={flash}
            value={radar[key]}
            moved={before !== null && before[key] !== radar[key]}
          />
        ))}
      </div>
    </div>
  );
}

function Meter({
  glyph,
  lit,
  flash,
  value,
  moved,
}: {
  glyph: string;
  lit: string;
  flash: string;
  value: number;
  moved: boolean;
}) {
  const on = Math.round((Math.max(0, Math.min(100, value)) / 100) * SEGMENTS);

  return (
    <div className="flex items-center gap-2.5">
      <span className="w-3 text-center text-[11px] text-amber-700/80">{glyph}</span>
      <div
        // Remounting on every change replays the flash, even for a repeat value.
        key={moved ? `${value}-moved` : value}
        className={`flex flex-1 gap-[3px] rounded-sm ${moved ? "anim-meter-flash" : ""} ${flash}`}
      >
        {Array.from({ length: SEGMENTS }, (_, i) => (
          <span
            key={i}
            className={`h-2.5 flex-1 rounded-[1px] transition-colors duration-300 ${
              i < on ? lit : "bg-zinc-800"
            }`}
            // Staggered so the row fills like a gauge sweeping up, not a jump.
            style={{ transitionDelay: `${i * 22}ms` }}
          />
        ))}
      </div>
    </div>
  );
}
