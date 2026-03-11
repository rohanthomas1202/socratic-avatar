"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAudioPlayback } from "@/hooks/useAudioPlayback";
import { AudioCapture } from "@/components/AudioCapture";
import { AvatarView } from "@/components/AvatarView";
import { SessionControls } from "@/components/SessionControls";
import type { AvatarMode, Concept, ServerMessage, SocraticState, TurnMetrics } from "@/lib/types";

interface ConversationEntry {
  role: "user" | "assistant";
  text: string;
}

export function TutorSession() {
  const [avatarMode, setAvatarMode] = useState<AvatarMode>("listening");
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  const [currentResponse, setCurrentResponse] = useState("");
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [metrics, setMetrics] = useState<TurnMetrics | null>(null);
  const [activeConcept, setActiveConcept] = useState<Concept | null>(null);
  const [simliConnected, setSimliConnected] = useState(false);
  const [socraticState, setSocraticState] = useState<SocraticState | null>(null);
  const [activeModel, setActiveModel] = useState<string | null>(null);

  // Ref to accumulate streaming response (avoids React strict mode double-fire)
  const responseRef = useRef("");

  // Ref to access AvatarView's video element for Simli audio feed
  const avatarVideoRef = useRef<HTMLVideoElement | null>(null);

  // Auto-scroll conversation feed
  const feedRef = useRef<HTMLDivElement>(null);

  const { playChunk, stop: stopPlayback } = useAudioPlayback();

  const handleServerMessage = useCallback(
    (msg: ServerMessage) => {
      // Track socratic state from any message that includes it
      if (msg.socratic_state) {
        setSocraticState(msg.socratic_state);
      }
      if (msg.model) {
        setActiveModel(msg.model);
      }

      switch (msg.type) {
        case "speech_started":
          setAvatarMode("listening");
          setCurrentTranscript("Listening...");
          break;

        case "speech_ended":
          setAvatarMode("thinking");
          setCurrentTranscript("Processing...");
          break;

        case "session_started":
          setSocraticState(msg.socratic_state || "opening");
          break;

        case "transcript":
          setCurrentTranscript(msg.text || "");
          setAvatarMode("thinking");
          if (msg.text) {
            setConversation((prev) => [...prev, { role: "user", text: msg.text! }]);
          }
          break;

        case "llm_ttft":
          setAvatarMode("speaking");
          responseRef.current = "";
          setCurrentResponse("");
          break;

        case "token":
          responseRef.current += (msg.text || "");
          setCurrentResponse(responseRef.current);
          break;

        case "turn_complete": {
          setAvatarMode("listening");
          setCurrentTranscript("");
          const finalText = msg.text || responseRef.current;
          if (finalText) {
            setConversation((c) => [...c, { role: "assistant", text: finalText }]);
          }
          responseRef.current = "";
          setCurrentResponse("");
          if (msg.metrics) {
            setMetrics(msg.metrics);
          }
          break;
        }

        case "session_reset":
          setConversation([]);
          setCurrentResponse("");
          setCurrentTranscript("");
          setMetrics(null);
          setAvatarMode("listening");
          setSocraticState(null);
          setActiveModel(null);
          break;
      }
    },
    []
  );

  // Track simli state in a ref so the audio callback always has the latest value
  const simliConnectedRef = useRef(false);
  simliConnectedRef.current = simliConnected;

  const handleAudio = useCallback(
    (data: ArrayBuffer) => {
      playChunk(data);

      const videoEl = avatarVideoRef.current as
        | (HTMLVideoElement & { avatarApi?: { sendAudio: (d: ArrayBuffer) => void } })
        | null;
      if (videoEl?.avatarApi && simliConnectedRef.current) {
        videoEl.avatarApi.sendAudio(data);
      }
    },
    [playChunk]
  );

  const { status, connect, disconnect, sendJson, sendBinary } = useWebSocket({
    onMessage: handleServerMessage,
    onAudio: handleAudio,
  });

  const handleStart = useCallback(
    (concept: Concept) => {
      setActiveConcept(concept);
      setConversation([]);
      setCurrentResponse("");
      setMetrics(null);
      setSocraticState("opening");
      setActiveModel(null);
      connect();
      // Send session_start with concept_id after connection opens
      // We use a small delay to ensure WS is open
      setTimeout(() => {
        sendJson({ type: "session_start", concept_id: concept.id });
      }, 500);
    },
    [connect, sendJson]
  );

  const handleStop = useCallback(() => {
    disconnect();
    stopPlayback();
    setAvatarMode("listening");
    setActiveConcept(null);
    setCurrentResponse("");
    setCurrentTranscript("");
    setSimliConnected(false);
    setSocraticState(null);
    setActiveModel(null);
  }, [disconnect, stopPlayback]);

  const handleTextSubmit = useCallback(
    (text: string) => {
      sendJson({ type: "text_input", text });
      setAvatarMode("thinking");
      setCurrentTranscript(text);
    },
    [sendJson]
  );

  const handleAudioChunk = useCallback(
    (chunk: ArrayBuffer) => {
      sendBinary(chunk);
    },
    [sendBinary]
  );

  const handleAvatarModeChange = useCallback((mode: AvatarMode) => {
    setAvatarMode(mode);
  }, []);

  const handleSimliConnected = useCallback((connected: boolean) => {
    setSimliConnected(connected);
  }, []);

  const avatarRefCallback = useCallback((node: HTMLDivElement | null) => {
    if (node) {
      const video = node.querySelector("video");
      avatarVideoRef.current = video;
    }
  }, []);

  // Auto-scroll to bottom when conversation or streaming response updates
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [conversation, currentResponse, currentTranscript]);

  const isConnected = status === "connected";

  return (
    <div className="tutor-session">
      {/* Avatar */}
      <div ref={avatarRefCallback}>
        <AvatarView
          active={isConnected}
          avatarMode={avatarMode}
          onModeChange={handleAvatarModeChange}
          onConnectionChange={handleSimliConnected}
        />
      </div>

      {activeConcept && (
        <div className="concept-badge">
          Topic: {activeConcept.name}
          {socraticState && (
            <span className="socratic-state-badge">
              {socraticState.toUpperCase()}
            </span>
          )}
          {activeModel && (
            <span className="model-badge">
              {activeModel}
            </span>
          )}
        </div>
      )}

      {/* Conversation feed */}
      <div className="conversation-feed" ref={feedRef}>
        {conversation.map((entry, i) => (
          <div key={i} className={`message ${entry.role}`}>
            <span className="message-role">
              {entry.role === "user" ? "You" : "Tutor"}
            </span>
            <p className="message-text">{entry.text}</p>
          </div>
        ))}

        {currentResponse && (
          <div className="message assistant streaming">
            <span className="message-role">Tutor</span>
            <p className="message-text">{currentResponse}<span className="cursor">&#9610;</span></p>
          </div>
        )}

        {currentTranscript && isConnected && (
          <div className="status-line">{currentTranscript}</div>
        )}
      </div>

      {/* Metrics bar */}
      {metrics && (
        <div className="metrics-bar">
          <span>STT: {metrics.stt_ms}ms</span>
          <span>LLM TTFT: {metrics.llm_ttft_ms}ms</span>
          <span>LLM Total: {metrics.llm_total_ms}ms</span>
          <span>TTS: {metrics.tts_first_ms}ms</span>
          <span>E2E: {metrics.e2e_ms}ms</span>
        </div>
      )}

      {/* Controls */}
      <SessionControls
        status={status}
        onStart={handleStart}
        onStop={handleStop}
        onTextSubmit={handleTextSubmit}
      />

      {/* Audio capture (invisible) */}
      <AudioCapture active={isConnected} onAudioChunk={handleAudioChunk} />
    </div>
  );
}
