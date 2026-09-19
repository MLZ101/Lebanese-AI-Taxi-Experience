import qrJouni from "../assets/qr-jouni.png";
import qrMalli from "../assets/qr-malli.png";

/**
 * The staff roll, after the game-over card.
 *
 * Every cabinet ended on one, so the credits are the natural place to put the
 * people who made it - no "about" link bolted onto the chrome.
 *
 * The codes are redrawn from the originals at four pixels a module, in cab
 * black on parchment, with the spec's four-module quiet zone baked in.
 * That is a functional requirement as much as a stylistic one: the originals
 * were mid-grey on white, which a phone struggles with, and the project sets
 * `image-rendering: pixelated` on every img, so a 1080px code shrunk to
 * thumbnail size would have had modules nearest-neighboured away. Both widths
 * below are whole multiples of the 37-module grid (3px and 4px a module), so
 * the blocks stay exact at either size. Do not swap them for arbitrary ones.
 */

const CREW = [
  {
    name: "HUSSEIN JOUNI",
    qr: qrJouni,
    href: "https://www.linkedin.com/in/hussein-jouni/",
  },
  {
    name: "MALLI",
    qr: qrMalli,
    href: "https://www.linkedin.com/in/mhmalli",
  },
] as const;

export function CreditsPanel() {
  return (
    <section className="bevel dash-plastic mt-1 px-3 py-3">
      <p className="text-center font-pixel text-[6px] tracking-[0.25em] text-taxi-dk sm:text-[8px]">
        ◈ STAFF ROLL ◈
      </p>

      <div className="mt-3 flex items-start justify-center gap-3 sm:gap-5">
        {CREW.map(({ name, qr, href }) => (
          <a
            key={name}
            href={href}
            target="_blank"
            rel="noreferrer noopener"
            className="group flex flex-col items-center gap-2"
          >
            {/* The tile matches the code's own quiet zone exactly, so there is
                no rectangle edge - it reads as something printed and taped to
                the dash rather than an image dropped on the glass. */}
            <span className="bevel-in block bg-parch p-1 transition-transform group-hover:-translate-y-0.5">
              <img
                src={qr}
                alt={`LinkedIn QR code for ${name}`}
                className="block w-[111px] sm:w-[148px]"
              />
            </span>

            <span className="text-center font-pixel text-[7px] leading-relaxed text-taxi group-hover:text-taxi-hi sm:text-[9px]">
              {name}
            </span>
          </a>
        ))}
      </div>

      <p className="anim-blink-soft mt-3 text-center font-pixel text-[6px] tracking-[0.25em] text-khaki sm:text-[8px]">
        SCAN OR TAP TO CONNECT
      </p>
    </section>
  );
}
