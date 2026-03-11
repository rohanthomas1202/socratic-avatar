"use client";

import { useCallback, useRef, useState } from "react";

const SAMPLE_RATE = 16000;
const CHUNK_SIZE = 4096; // ~256ms at 16kHz mono 16-bit

interface UseAudioStreamOptions {
  onAudioChunk?: (chunk: ArrayBuffer) => void;
}

export function useAudioStream(options: UseAudioStreamOptions = {}) {
  const { onAudioChunk } = options;
  const [isCapturing, setIsCapturing] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const callbackRef = useRef(onAudioChunk);
  callbackRef.current = onAudioChunk;

  const startCapture = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      const context = new AudioContext({ sampleRate: SAMPLE_RATE });
      contextRef.current = context;

      const source = context.createMediaStreamSource(stream);

      // ScriptProcessorNode for PCM16 conversion
      // (AudioWorklet would be better for production, but this is simpler)
      const processor = context.createScriptProcessor(CHUNK_SIZE, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        const float32 = event.inputBuffer.getChannelData(0);
        const pcm16 = float32ToPcm16(float32);
        callbackRef.current?.(pcm16.buffer as ArrayBuffer);
      };

      source.connect(processor);
      processor.connect(context.destination);

      setIsCapturing(true);
    } catch (err) {
      console.error("Failed to capture audio:", err);
      throw err;
    }
  }, []);

  const stopCapture = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (contextRef.current) {
      contextRef.current.close();
      contextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setIsCapturing(false);
  }, []);

  return { isCapturing, startCapture, stopCapture };
}

/** Convert Float32 audio samples to Int16 PCM bytes. */
function float32ToPcm16(float32: Float32Array): Int16Array {
  const pcm16 = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return pcm16;
}
