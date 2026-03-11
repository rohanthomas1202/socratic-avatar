"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ClientMessage, ServerMessage, SessionStatus } from "@/lib/types";

const WS_URL = "ws://localhost:8050/ws/session";
const RECONNECT_DELAY = 2000;
const PING_INTERVAL = 15000;

interface UseWebSocketOptions {
  onMessage?: (msg: ServerMessage) => void;
  onAudio?: (data: ArrayBuffer) => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onMessage, onAudio, autoConnect = false } = options;
  const [status, setStatus] = useState<SessionStatus>("idle");
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const callbacksRef = useRef({ onMessage, onAudio });

  // Keep callbacks fresh without re-triggering effects
  useEffect(() => {
    callbacksRef.current = { onMessage, onAudio };
  }, [onMessage, onAudio]);

  const cleanup = useCallback(() => {
    if (pingRef.current) {
      clearInterval(pingRef.current);
      pingRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    cleanup();
    setStatus("connecting");

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.binaryType = "arraybuffer";

    ws.onopen = () => {
      setStatus("connected");
      // Start ping keepalive
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        callbacksRef.current.onAudio?.(event.data);
      } else {
        try {
          const msg: ServerMessage = JSON.parse(event.data);
          callbacksRef.current.onMessage?.(msg);
        } catch {
          console.warn("Failed to parse WS message:", event.data);
        }
      }
    };

    ws.onclose = () => {
      setStatus("idle");
      cleanup();
    };

    ws.onerror = () => {
      setStatus("error");
    };
  }, [cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    setStatus("idle");
  }, [cleanup]);

  const sendJson = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const sendBinary = useCallback((data: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  // Auto-connect if requested
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return cleanup;
  }, [autoConnect, connect, cleanup]);

  return { status, connect, disconnect, sendJson, sendBinary };
}
