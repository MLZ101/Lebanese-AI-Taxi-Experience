import abuFadi from "../assets/abu-fadi.jpeg";
import type { ModelOption } from "../types";
import { ModelPicker } from "./ModelPicker";

/**
 * Attract screen.
 *
 * Built to look like a cartridge boot: marquee art behind the logo, a blinking
 * START prompt, and a run of fake cabinet furniture (player count, a bogus
 * copyright, a scrolling ticker) that sells the era without claiming anything
 * real. The button is a real button at all times - the blink is on a sibling
 * label, so if the animation layer dies the player can still get in the car.
 */

interface Props {
  onStart: () => void;
  starting: boolean;
  error: string | null;
  models: ModelOption[];
  model: string | undefined;
  onModel: (id: string) => void;
}

export function TitleScreen({
  onStart,
  starting,
  error,
  models,
  model,
  onModel,
}: Props) {
  return (
    <div className="relative flex h-full flex-col items-center justify-between overflow-hidden px-4 py-5 text-center sm:px-8 sm:py-8">
      {/* Marquee art, pushed right back so the logo stays legible. */}
      <img
        src={abuFadi}
        alt=""
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-20 brightness-75 saturate-150"
      />
      <div
        aria-hidden="true"
        className="crt-vignette pointer-events-none absolute inset-0"
      />

      {/* Cabinet top strip. */}
      <div className="relative flex w-full items-center justify-between font-pixel text-[7px] text-taxi-dk sm:text-[9px]">
        <span>1 PLAYER</span>
        <span className="anim-blink-soft text-cedar">◈ INSERT COIN</span>
        <span>HI 99999</span>
      </div>

      <div className="relative flex flex-col items-center gap-5 sm:gap-7">
        <p className="font-pixel text-[7px] tracking-[0.3em] text-dust sm:text-[10px]">
          BEIRUT — SOMETIME AFTER 6PM
        </p>

        <h1 className="anim-bob font-pixel text-[7vw] leading-[1.7] sm:text-3xl lg:text-4xl">
          <span className="pix-title block">THE LEBANESE</span>
          <span className="pix-title mt-3 block sm:mt-5">TAXI EXPERIENCE</span>
        </h1>

        {/* Loud little subtitle plate, like a bootleg cart label. */}
        <p className="bevel-gold px-3 py-1.5 font-pixel text-[7px] sm:px-4 sm:text-[10px]">
          ★ HE IS GOING TO ASK ★
        </p>

        <p className="max-w-xl text-pretty font-term text-lg leading-tight text-bone sm:text-2xl">
          A service taxi stops. The door is already open.
          <br />
          <span className="text-dust">
            Abu Fadi wants to know exactly who he picked up.
          </span>
        </p>

        <div className="mt-1 flex flex-col items-center gap-3.5">
          <ModelPicker
            models={models}
            value={model}
            disabled={starting}
            onChange={onModel}
          />

          <button
            type="button"
            onClick={onStart}
            disabled={starting}
            className="bevel-gold px-6 py-3.5 font-pixel text-[10px] tracking-wider hover:bg-taxi-hi disabled:opacity-60 sm:px-10 sm:text-sm"
          >
            {starting ? "GETTING IN..." : error ? "▶ TRY AGAIN" : "▶ GET IN"}
          </button>

          {!starting && (
            <span className="anim-blink font-pixel text-[7px] text-taxi sm:text-[9px]">
              PRESS START
            </span>
          )}
        </div>

        {error && (
          <p className="bevel-in max-w-sm px-3 py-2 font-term text-lg text-blood">
            ! {error}
          </p>
        )}
      </div>

      {/* Cabinet bottom strip. */}
      <div className="relative w-full space-y-2">
        <Ticker />
        <p className="font-pixel text-[6px] text-taxi-dk sm:text-[8px]">
          © 1997 BEIRUT SOFTWORKS — ALL RIGHTS RESERVED
        </p>
      </div>
    </div>
  );
}

/** Attract-mode ticker. Pure decoration, so it is hidden from screen readers. */
function Ticker() {
  const line =
    "NO SEATBELTS · NO METER · NO ESCAPE · ANSWER CAREFULLY · HE IS WATCHING THE MIRROR";

  return (
    <div
      aria-hidden="true"
      className="bevel-in overflow-hidden px-2 py-1 font-pixel text-[6px] text-khaki sm:text-[8px]"
    >
      <p className="whitespace-nowrap">{line}</p>
    </div>
  );
}
