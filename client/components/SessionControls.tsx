"use client";

import { useState } from "react";
import type { Concept, SessionStatus } from "@/lib/types";
import { CONCEPTS } from "@/lib/types";

interface SessionControlsProps {
  status: SessionStatus;
  onStart: (concept: Concept) => void;
  onStop: () => void;
  onTextSubmit: (text: string) => void;
}

export function SessionControls({
  status,
  onStart,
  onStop,
  onTextSubmit,
}: SessionControlsProps) {
  const [selectedConcept, setSelectedConcept] = useState<string>(CONCEPTS[0].id);
  const [textInput, setTextInput] = useState("");

  const handleStart = () => {
    const concept = CONCEPTS.find((c) => c.id === selectedConcept);
    if (concept) onStart(concept);
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onTextSubmit(textInput.trim());
      setTextInput("");
    }
  };

  const isConnected = status === "connected";

  return (
    <div className="session-controls">
      {!isConnected ? (
        <div className="start-panel">
          <label htmlFor="concept-select">Choose a topic:</label>
          <select
            id="concept-select"
            value={selectedConcept}
            onChange={(e) => setSelectedConcept(e.target.value)}
          >
            {CONCEPTS.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} — {c.description}
              </option>
            ))}
          </select>
          <button
            className="btn btn-primary"
            onClick={handleStart}
            disabled={status === "connecting"}
          >
            {status === "connecting" ? "Connecting..." : "Start Session"}
          </button>
        </div>
      ) : (
        <div className="active-panel">
          <form onSubmit={handleTextSubmit} className="text-input-form">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type a message (or just speak)..."
              className="text-input"
            />
            <button type="submit" className="btn btn-send" disabled={!textInput.trim()}>
              Send
            </button>
          </form>
          <button className="btn btn-stop" onClick={onStop}>
            End Session
          </button>
        </div>
      )}
    </div>
  );
}
