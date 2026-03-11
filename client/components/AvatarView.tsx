"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { AvatarMode } from "@/lib/types";
import { createSimliSession, type SimliSession } from "@/lib/simli";

interface AvatarViewProps {
  active: boolean;
  avatarMode: AvatarMode;
  onModeChange?: (mode: AvatarMode) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export function AvatarView({ active, avatarMode, onModeChange, onConnectionChange }: AvatarViewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const sessionRef = useRef<SimliSession | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize Simli session when active
  useEffect(() => {
    if (!active || !videoRef.current || !audioRef.current) {
      return;
    }

    let cancelled = false;

    const init = async () => {
      try {
        setError(null);
        const session = await createSimliSession(
          videoRef.current!,
          audioRef.current!,
          () => onModeChange?.("speaking"),
          () => onModeChange?.("listening"),
          (msg) => {
            console.error("Simli error:", msg);
            setError(msg);
          }
        );

        if (cancelled) {
          session.stop();
          return;
        }

        sessionRef.current = session;
        // Mute Simli's audio output (we play TTS via Web Audio API)
        if (audioRef.current) {
          audioRef.current.volume = 0;
        }
        setConnected(true);
        onConnectionChange?.(true);
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          console.error("Failed to initialize Simli:", msg);
          setError(msg);
        }
      }
    };

    init();

    return () => {
      cancelled = true;
      if (sessionRef.current) {
        sessionRef.current.stop();
        sessionRef.current = null;
      }
      setConnected(false);
      onConnectionChange?.(false);
    };
  }, [active, onModeChange, onConnectionChange]);

  // Expose sendAudio for parent to call
  const sendAudio = useCallback((pcm16: ArrayBuffer) => {
    sessionRef.current?.sendAudio(pcm16);
  }, []);

  const clearBuffer = useCallback(() => {
    sessionRef.current?.clearBuffer();
  }, []);

  // Store sendAudio/clearBuffer on a ref so parent can access via ref
  const apiRef = useRef({ sendAudio, clearBuffer });
  apiRef.current = { sendAudio, clearBuffer };

  // Attach apiRef to video element's dataset for parent access
  useEffect(() => {
    if (videoRef.current) {
      (videoRef.current as HTMLVideoElement & { avatarApi?: typeof apiRef.current }).avatarApi = apiRef.current;
    }
  });

  return (
    <div className="avatar-area">
      <div className={`avatar-container ${avatarMode} ${connected ? "connected" : ""}`}>
        {/* Simli video element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="avatar-video"
          style={{ display: connected ? "block" : "none" }}
        />
        {/* Simli needs an audio element for WebRTC. Keep unmuted for WebRTC init,
            but volume=0 since we play TTS through Web Audio API */}
        <audio ref={audioRef} autoPlay playsInline />

        {/* Fallback placeholder when not connected */}
        {!connected && (
          <div className="avatar-placeholder-inner">
            <div className="avatar-icon">
              {avatarMode === "listening" && "\uD83D\uDC42"}
              {avatarMode === "thinking" && "\uD83E\uDD14"}
              {avatarMode === "speaking" && "\uD83D\uDDE3\uFE0F"}
            </div>
            <span className="avatar-status">
              {error ? "Avatar unavailable" : active ? "Connecting avatar..." : avatarMode}
            </span>
          </div>
        )}

        {/* Mode indicator overlay */}
        {connected && (
          <div className="avatar-mode-overlay">
            <span className={`mode-dot ${avatarMode}`} />
            <span className="mode-label">{avatarMode}</span>
          </div>
        )}
      </div>

      {error && <div className="avatar-error">{error}</div>}
    </div>
  );
}

// Export ref type for parent to use
export type AvatarViewHandle = {
  sendAudio: (pcm16: ArrayBuffer) => void;
  clearBuffer: () => void;
};
