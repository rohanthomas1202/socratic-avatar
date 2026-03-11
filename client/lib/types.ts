/** Socratic state machine states */
export type SocraticState =
  | "opening"
  | "probe"
  | "scaffold"
  | "redirect"
  | "confirm"
  | "deepen"
  | "close";

/** WebSocket message types from server */
export type ServerMessageType =
  | "speech_started"
  | "speech_ended"
  | "transcript"
  | "llm_ttft"
  | "token"
  | "sentence"
  | "turn_complete"
  | "session_reset"
  | "session_started"
  | "pong";

export interface ServerMessage {
  type: ServerMessageType;
  turn_id?: number;
  text?: string;
  stt_ms?: number;
  ttft_ms?: number;
  metrics?: TurnMetrics;
  socratic_state?: SocraticState;
  model?: string;
  concept_id?: string;
}

export interface TurnMetrics {
  stt_ms: number;
  llm_ttft_ms: number;
  llm_total_ms: number;
  tts_first_ms: number;
  e2e_ms: number;
}

/** WebSocket message types to server */
export type ClientMessageType = "text_input" | "reset" | "ping" | "session_start";

export interface ClientMessage {
  type: ClientMessageType;
  text?: string;
  concept_id?: string;
}

/** Session state */
export type SessionStatus = "idle" | "connecting" | "connected" | "error";
export type AvatarMode = "listening" | "thinking" | "speaking";

export interface SessionState {
  status: SessionStatus;
  avatarMode: AvatarMode;
  currentTranscript: string;
  currentResponse: string;
  turnId: number;
  metrics: TurnMetrics | null;
  error: string | null;
}

/** Concept for the tutor to teach */
export interface Concept {
  id: string;
  name: string;
  description: string;
}

export const CONCEPTS: Concept[] = [
  { id: "division_by_zero", name: "Division by Zero", description: "Why can't we divide by zero?" },
  { id: "photosynthesis", name: "Photosynthesis", description: "How do plants make food from sunlight?" },
  { id: "gravity", name: "Gravity", description: "Why do things fall down?" },
  { id: "fractions", name: "Fractions", description: "What does 1/2 really mean?" },
  { id: "water_cycle", name: "Water Cycle", description: "Where does rain come from?" },
];
