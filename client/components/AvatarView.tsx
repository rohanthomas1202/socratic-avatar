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

  // Keep callbacks in refs so the effect doesn't re-fire when they change
  const onModeChangeRef = useRef(onModeChange);
  onModeChangeRef.current = onModeChange;
  const onConnectionChangeRef = useRef(onConnectionChange);
  onConnectionChangeRef.current = onConnectionChange;

  // Track cleanup state
  const cleaningUpRef = useRef(false);

  // Only depends on `active` — callbacks accessed via refs
  useEffect(() => {
    if (!active || !videoRef.current || !audioRef.current) {
      return;
    }

    let cancelled = false;

    const init = async () => {
      // Wait for any ongoing cleanup (max 3 seconds)
      const deadline = Date.now() + 3000;
      while (cleaningUpRef.current && Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, 200));
      }
      cleaningUpRef.current = false; // Force clear if timed out

      if (cancelled) return;

      try {
        setError(null);
        const session = await createSimliSession(
          videoRef.current!,
          audioRef.current!,
          () => onModeChangeRef.current?.("speaking"),
          () => onModeChangeRef.current?.("listening"),
          (msg) => {
            console.error("Simli error:", msg);
            setError(msg);
          }
        );

        if (cancelled) {
          session.stop().catch(() => {});
          return;
        }

        sessionRef.current = session;
        if (audioRef.current) {
          audioRef.current.volume = 0;
        }
        setConnected(true);
        onConnectionChangeRef.current?.(true);
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
      const session = sessionRef.current;
      sessionRef.current = null;
      setConnected(false);
      onConnectionChangeRef.current?.(false);

      if (session) {
        cleaningUpRef.current = true;
        session.stop()
          .catch(() => {})
          .finally(() => {
            cleaningUpRef.current = false;
          });
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

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

  // Attach apiRef to video element for parent access
  useEffect(() => {
    if (videoRef.current) {
      (videoRef.current as HTMLVideoElement & { avatarApi?: typeof apiRef.current }).avatarApi = apiRef.current;
    }
  });

  return (
    <div className="avatar-area">
      <div className={`avatar-container ${avatarMode} ${connected ? "connected" : ""}`}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          className="avatar-video"
          style={{ display: connected ? "block" : "none" }}
        />
        <audio ref={audioRef} autoPlay playsInline />

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

export type AvatarViewHandle = {
  sendAudio: (pcm16: ArrayBuffer) => void;
  clearBuffer: () => void;
};
