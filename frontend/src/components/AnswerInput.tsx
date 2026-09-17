import { useEffect, useRef, useState } from "react";

/** The only way to talk back. Locked while Abu Fadi is thinking. */

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
    <div className="flex gap-2">
      <input
        ref={inputRef}
        value={text}
        disabled={disabled}
        maxLength={500}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder={waiting ? "Abu Fadi is thinking..." : "Say something..."}
        className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900/80 px-4 py-3 text-zinc-100 placeholder-zinc-600 outline-none transition focus:border-amber-600/70 disabled:opacity-50"
      />
      <button
        type="button"
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="rounded-lg bg-amber-500 px-5 py-3 font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:bg-zinc-700 disabled:text-zinc-500"
      >
        Reply
      </button>
    </div>
  );
}
