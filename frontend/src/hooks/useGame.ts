import { useCallback, useRef, useState } from "react";

import { ApiError, sendAnswer, startGame } from "../api/client";
import type { GameState } from "../types";

/**
 * The whole client-side game state. One hook, no state library - the game is
 * a single object plus a status flag.
 */
export type Phase = "idle" | "starting" | "ready" | "thinking" | "ended" | "error";

export function useGame() {
  const [state, setState] = useState<GameState | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);

  /** Guards against double submits racing each other past the disabled input. */
  const busy = useRef(false);

  const run = useCallback(
    async (work: () => Promise<GameState>, pending: Phase) => {
      if (busy.current) return;
      busy.current = true;
      setPhase(pending);
      setError(null);
      try {
        const next = await work();
        setState(next);
        setPhase(next.game_status === "ended" ? "ended" : "ready");
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Something went wrong.");
        setPhase("error");
      } finally {
        busy.current = false;
      }
    },
    [],
  );

  const start = useCallback(() => run(startGame, "starting"), [run]);

  const answer = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!state || !trimmed || state.game_status === "ended") return;
      return run(() => sendAnswer(state.session_id, trimmed), "thinking");
    },
    [run, state],
  );

  /** True while Abu Fadi is working - the input stays locked. */
  const waiting = phase === "starting" || phase === "thinking";

  const canAnswer = Boolean(state) && phase === "ready";

  return { state, phase, error, waiting, canAnswer, start, answer };
}
