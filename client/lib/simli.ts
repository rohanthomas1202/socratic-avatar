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
  // 1. Get session token from server
  const resp = await fetch(SIMLI_TOKEN_URL, { method: "POST" });
  if (!resp.ok) {
    throw new Error(`Failed to get Simli token: ${resp.status}`);
  }
  const data = await resp.json();

  // The server returns the session metadata from Simli's API
  // which includes a session_token or similar field
  const sessionToken = data.session_token || data.sessionToken || "";
  if (!sessionToken) {
    throw new Error("No session token returned from server");
  }

  // 2. Create SimliClient
  const client = new SimliClient(
    sessionToken,
    videoEl,
    audioEl,
    null,         // ICE servers (null = default)
    LogLevel.INFO,
    "livekit"     // Transport mode
  );

  // 3. Register events
  if (onSpeaking) client.on("speaking", onSpeaking);
  if (onSilent) client.on("silent", onSilent);
  if (onError) client.on("error", onError);

  // 4. Start the connection
  await client.start();

  return {
    client,
    sendAudio: (pcm16: ArrayBuffer) => {
      client.sendAudioData(new Uint8Array(pcm16));
    },
    stop: () => client.stop(),
    clearBuffer: () => client.ClearBuffer(),
  };
}
