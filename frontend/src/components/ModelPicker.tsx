import type { ModelOption } from "../types";

/**
 * Which brain drives Abu Fadi. Chosen before the ride starts - a session keeps
 * its model for the whole conversation.
 *
 * Dressed as a cabinet DIP switch rather than a settings control: it belongs to
 * the machine, not to the game. Models whose provider has no API key come back
 * flagged unavailable and are shown disabled, so it is obvious what is on offer.
 */

interface Props {
  models: ModelOption[];
  value: string | undefined;
  disabled: boolean;
  onChange: (id: string) => void;
}

export function ModelPicker({ models, value, disabled, onChange }: Props) {
  if (models.length === 0) return null;
  const usable = models.filter((m) => m.available);

  return (
    <label className="flex flex-col items-center gap-1.5">
      <span className="font-pixel text-[6px] tracking-[0.25em] text-taxi-dk sm:text-[8px]">
        DRIVER BRAIN
      </span>
      <select
        value={value ?? usable[0]?.id ?? ""}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="bevel-in max-w-[85vw] px-2 py-1.5 font-term text-lg text-bone outline-none disabled:opacity-50 sm:px-3"
      >
        {models.map((m) => (
          <option key={m.id} value={m.id} disabled={!m.available}>
            {m.label}
            {m.note ? ` - ${m.note}` : ""}
            {m.available ? "" : " (NO KEY)"}
          </option>
        ))}
      </select>
    </label>
  );
}
