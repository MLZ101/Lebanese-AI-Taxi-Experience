import type { GameState, ModelOption } from "../types";

/** Empty in dev - vite proxies /game to the backend. Set for deployment. */
const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Can't reach Abu Fadi. Is the backend running?", 0);
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((d) => d?.detail)
      .catch(() => null);
    throw new ApiError(
      typeof detail === "string" ? detail : `Request failed (${response.status})`,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

export const startGame = (model?: string) =>
  post<GameState>("/game/start", { model: model ?? null });

/** The catalog of brains. Failing to load it is not fatal - the backend picks. */
export async function fetchModels(): Promise<ModelOption[]> {
  try {
    const response = await fetch(`${BASE}/ai/models`);
    if (!response.ok) return [];
    return (await response.json()).models ?? [];
  } catch {
    return [];
  }
}

export const sendAnswer = (sessionId: string, answer: string) =>
  post<GameState>("/game/answer", { session_id: sessionId, answer });
