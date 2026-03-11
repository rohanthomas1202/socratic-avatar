"use client";

import { useCallback, useRef } from "react";

const SAMPLE_RATE = 16000;

/**
 * Plays back PCM16 audio chunks received from the server
 * using the Web Audio API.
 */
export function useAudioPlayback() {
  const contextRef = useRef<AudioContext | null>(null);
  const nextTimeRef = useRef(0);

  const getContext = useCallback(() => {
    if (!contextRef.current || contextRef.current.state === "closed") {
      contextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
      nextTimeRef.current = 0;
    }
    return contextRef.current;
  }, []);

  const playChunk = useCallback(
    (audioData: ArrayBuffer) => {
      if (!audioData.byteLength || audioData.byteLength < 2) return;

      const ctx = getContext();

      // Server sends raw PCM16 bytes (16kHz mono)
      // Trim to even length if needed
      const byteLen = audioData.byteLength - (audioData.byteLength % 2);
      const pcm16 = new Int16Array(audioData, 0, byteLen / 2);
      const float32 = new Float32Array(pcm16.length);
      for (let i = 0; i < pcm16.length; i++) {
        float32[i] = pcm16[i] / 0x8000;
      }

      const buffer = ctx.createBuffer(1, float32.length, SAMPLE_RATE);
      buffer.getChannelData(0).set(float32);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);

      // Schedule chunks sequentially to avoid gaps
      const now = ctx.currentTime;
      const startTime = Math.max(now, nextTimeRef.current);
      source.start(startTime);
      nextTimeRef.current = startTime + buffer.duration;
    },
    [getContext]
  );

  const stop = useCallback(() => {
    if (contextRef.current && contextRef.current.state !== "closed") {
      contextRef.current.close();
      contextRef.current = null;
    }
    nextTimeRef.current = 0;
  }, []);

  return { playChunk, stop };
}
