import { SimliClient, LogLevel } from "simli-client";

const SIMLI_TOKEN_URL = "http://localhost:8050/api/simli/token";

export interface SimliSession {
  client: SimliClient;
  sendAudio: (pcm16: ArrayBuffer) => void;
  stop: () => Promise<void>;
  clearBuffer: () => void;
}

/**
 * Fetch a Simli session token from our backend,
 * then initialize and start a SimliClient.
 */
export async function createSimliSession(
  videoEl: HTMLVideoElement,
  audioEl: HTMLAudioElement,
  onSpeaking?: () => void,
  onSilent?: () => void,
  onError?: (msg: string) => void
): Promise<SimliSession> {
  // 1. Get session token + ICE servers from server
  console.log("[Simli] Fetching session token...");
  const resp = await fetch(SIMLI_TOKEN_URL, { method: "POST" });
  if (!resp.ok) {
    throw new Error(`Failed to get Simli token: ${resp.status}`);
  }
  const data = await resp.json();
  console.log("[Simli] Token response:", JSON.stringify(data));

  const sessionToken = data.session_token || data.sessionToken || "";
  if (!sessionToken) {
    throw new Error("No session token returned from server");
  }

  // Parse ICE servers from response
  const iceServers: RTCIceServer[] | null = data.ice_servers || null;
  console.log("[Simli] ICE servers:", iceServers ? "provided" : "null (using defaults)");

  // 2. Create SimliClient with ICE servers
  console.log("[Simli] Creating client with token:", sessionToken.slice(0, 20) + "...");
  const client = new SimliClient(
    sessionToken,
    videoEl,
    audioEl,
    iceServers,
    LogLevel.INFO,
    "livekit"
  );

  // 3. Register events
  if (onSpeaking) client.on("speaking", onSpeaking);
  if (onSilent) client.on("silent", onSilent);
  if (onError) client.on("error", onError);
  client.on("startup_error", (msg) => {
    console.error("[Simli] Startup error:", msg);
    onError?.(msg);
  });
  client.on("start", () => console.log("[Simli] Connected successfully"));

  // 4. Start the connection
  console.log("[Simli] Starting connection...");
  await client.start();
  console.log("[Simli] start() resolved");

  return {
    client,
    sendAudio: (pcm16: ArrayBuffer) => {
      client.sendAudioData(new Uint8Array(pcm16));
    },
    stop: () => client.stop(),
    clearBuffer: () => client.ClearBuffer(),
  };
}
