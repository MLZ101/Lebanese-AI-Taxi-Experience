/** Mirrors backend/app/schemas.py::PublicState. Keep the two in sync. */

export type Mood = "neutral" | "curious" | "suspicious" | "excited" | "upset";
export type DriverAction = "normal" | "mirror" | "nod" | "money";
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

export interface GameState {
  session_id: string;
  message_count: number;
  max_messages: number;
  game_status: GameStatus;
  end_reason: string | null;
  radar: Radar;
  question: string;
  thinking: string;
  mood: Mood;
  driver_action: DriverAction;
  history: Turn[];
  /** The AI call failed and the scripted driver stood in. */
  ai_degraded: boolean;
  /** Null in a demo build - see EXPOSE_DEBUG in the backend .env. */
  debug: DebugInfo | null;
}
