import { useEffect, useRef, useState } from "react";

/**
 * The only way to talk back. Locked while Abu Fadi is thinking.
 *
 * Styled as a sunken terminal field with a lit prompt caret and a character
 * budget in the corner, so typing feels like entering your initials on a
 * high-score table.
 */

const MAX = 500;

interface Props {
  disabled: boolean;
  waiting: boolean;
  onSubmit: (text: string) => void;
}

export function AnswerInput({ disabled, waiting, onSubmit }: Props) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Re-focus as soon as it's the player's turn again.
  useEffect(() => {
    if (!disabled) inputRef.current?.focus();
  }, [disabled]);

  const submit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText("");
  };

  return (
    <div>
      <div className="flex items-stretch gap-2">
        <div className="bevel-in relative flex flex-1 items-center gap-2 px-2">
          <span
            aria-hidden="true"
            className={`font-pixel text-[10px] ${
              disabled ? "text-khaki" : "anim-blink text-cedar"
            }`}
          >
            ▶
          </span>

          <input
            ref={inputRef}
            value={text}
            disabled={disabled}
            maxLength={MAX}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder={waiting ? "ABU FADI IS THINKING..." : "SAY SOMETHING"}
            aria-label="Your answer"
            className="min-w-0 flex-1 bg-transparent py-2.5 font-term text-xl text-bone caret-taxi outline-none placeholder:text-khaki disabled:opacity-60 sm:text-2xl"
          />
        </div>

        <button
          type="button"
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="bevel-gold shrink-0 px-3 font-pixel text-[9px] hover:bg-taxi-hi disabled:border-cab-hi disabled:bg-cab disabled:text-khaki sm:px-5 sm:text-[11px]"
        >
          SAY IT
        </button>
      </div>

      <div className="mt-1.5 flex justify-between font-pixel text-[6px] text-khaki sm:text-[8px]">
        <span>[ENTER] TO TALK</span>
        <span className={text.length > MAX - 50 ? "text-blood" : undefined}>
          {text.length}/{MAX}
        </span>
      </div>
    </div>
  );
}
