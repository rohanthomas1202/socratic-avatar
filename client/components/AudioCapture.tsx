"use client";

import { useEffect } from "react";
import { useAudioStream } from "@/hooks/useAudioStream";

interface AudioCaptureProps {
  active: boolean;
  onAudioChunk: (chunk: ArrayBuffer) => void;
}

/**
 * Invisible component that captures mic audio and sends PCM16 chunks.
 * Starts/stops capture based on the `active` prop.
 */
export function AudioCapture({ active, onAudioChunk }: AudioCaptureProps) {
  const { isCapturing, startCapture, stopCapture } = useAudioStream({
    onAudioChunk,
  });

  useEffect(() => {
    if (active && !isCapturing) {
      startCapture().catch(console.error);
    } else if (!active && isCapturing) {
      stopCapture();
    }
  }, [active, isCapturing, startCapture, stopCapture]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCapture();
    };
  }, [stopCapture]);

  return null;
}
