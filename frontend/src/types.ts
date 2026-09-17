/** Mirrors backend/app/schemas.py::PublicState. Keep the two in sync. */

export type Mood = "neutral" | "curious" | "suspicious" | "excited" | "upset";
export type GameStatus = "active" | "ended";
export type Speaker = "abu_fadi" | "passenger";

export interface Radar {
  money: number;
  status: number;
  suspicion: number;
  tip: number;
}

export interface Turn {
  role: Speaker;
  text: string;
}

/** Only present while the backend runs with EXPOSE_DEBUG=true. */
export interface DebugInfo {
  money_confidence: number;
  religion_confidence: number;
  confidence_threshold: number;
  soft_end_messages: number;
}

export interface ModelOption {
  id: string;
  label: string;
  provider: string;
  note: string;
  available: boolean;
}

/** Abu Fadi's conclusion. Only present once the ride has ended. */
export interface Verdict {
  /** The call itself - the ta2ifa he landed on. The payoff. */
  guess: string;
  if_right: string;
  if_wrong: string;
  money_verdict: string;
  background_verdict: string;
  evidence: string[];
  fare: string;
  closing_line: string;
}

export interface GameState {
  session_id: string;
  /** The model actually driving this ride, after the backend resolved it. */
  model: string;
  message_count: number;
  max_messages: number;
  game_status: GameStatus;
  end_reason: string | null;
  radar: Radar;
  question: string;
  thinking: string;
  mood: Mood;
  history: Turn[];
  /** The AI call failed and the scripted driver stood in. */
  ai_degraded: boolean;
  /** Null in a demo build - see EXPOSE_DEBUG in the backend .env. */
  debug: DebugInfo | null;
  /** Null while the ride is running. */
  verdict: Verdict | null;
}
