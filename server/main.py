import base64
import json
import logging
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from pipeline.orchestrator import PipelineOrchestrator
from pipeline.sentence_chunker import SentenceChunker
from pipeline.tts import ElevenLabsTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Socratic AI Video Tutor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/session")
async def websocket_session(ws: WebSocket):
    """WebSocket endpoint for a tutoring session.

    Protocol:
    - Client sends: binary audio chunks (PCM16, 16kHz, mono)
                    OR JSON text messages for control
    - Server sends: JSON messages with transcripts, tokens, metrics
                    Binary messages with TTS audio chunks
    """
    await ws.accept()
    orchestrator = PipelineOrchestrator()
    logger.info("WebSocket session connected")

    try:
        while True:
            message = await ws.receive()

            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]
                vad_result = orchestrator.process_audio_chunk(audio_bytes)

                if vad_result["speech_started"]:
                    await ws.send_json({"type": "speech_started"})

                if vad_result["speech_ended"]:
                    await ws.send_json({"type": "speech_ended"})

                    buffered_audio = orchestrator.vad.get_buffered_audio()
                    if buffered_audio:
                        async for event in orchestrator.process_turn_streaming(buffered_audio):
                            if event["type"] == "audio":
                                # Send audio as binary WebSocket frame
                                await ws.send_bytes(event["data"])
                            else:
                                await ws.send_json(event)

                    orchestrator.vad.reset()

            elif "text" in message and message["text"]:
                data = json.loads(message["text"])
                msg_type = data.get("type", "")

                if msg_type == "text_input":
                    # Text input with full streaming pipeline (LLM → Chunker → TTS)
                    text = data.get("text", "")
                    if text:
                        await _handle_text_turn(ws, orchestrator, text)

                elif msg_type == "reset":
                    orchestrator.reset()
                    await ws.send_json({"type": "session_reset"})

                elif msg_type == "ping":
                    await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket session disconnected")
    except RuntimeError as e:
        if "disconnect" in str(e).lower():
            logger.info("WebSocket session disconnected (runtime)")
        else:
            logger.error(f"WebSocket runtime error: {e}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await ws.close(code=1011, reason=str(e))
        except RuntimeError:
            pass


async def _handle_text_turn(ws: WebSocket, orchestrator: PipelineOrchestrator, text: str):
    """Handle a text-input turn with full streaming pipeline."""
    orchestrator.session.turn_count += 1
    turn_id = orchestrator.session.turn_count
    t_start = time.perf_counter()

    await ws.send_json({
        "type": "transcript",
        "turn_id": turn_id,
        "text": text,
        "stt_ms": 0,
    })

    # Stream LLM → Chunker → TTS
    chunker = SentenceChunker()
    tts = orchestrator.tts
    t_llm_start = time.perf_counter()
    first_token = True
    first_tts = True
    ttft_ms = 0.0
    tts_first_ms = 0.0
    full_response = []

    async for token in orchestrator.llm.generate_stream(
        user_message=text,
        conversation_history=orchestrator.session.conversation_history,
    ):
        if first_token:
            ttft_ms = (time.perf_counter() - t_llm_start) * 1000
            await ws.send_json({"type": "llm_ttft", "turn_id": turn_id, "ttft_ms": round(ttft_ms, 1)})
            first_token = False

        full_response.append(token)
        await ws.send_json({"type": "token", "turn_id": turn_id, "text": token})

        # Sentence chunking → TTS
        sentence = chunker.add_token(token)
        if sentence:
            await ws.send_json({"type": "sentence", "turn_id": turn_id, "text": sentence})
            async for audio_chunk in tts.synthesize_streaming(sentence):
                if first_tts:
                    tts_first_ms = (time.perf_counter() - t_llm_start) * 1000
                    first_tts = False
                await ws.send_bytes(audio_chunk)

    t_llm_end = time.perf_counter()

    # Flush remaining
    remaining = chunker.flush()
    if remaining:
        await ws.send_json({"type": "sentence", "turn_id": turn_id, "text": remaining})
        async for audio_chunk in tts.synthesize_streaming(remaining):
            if first_tts:
                tts_first_ms = (time.perf_counter() - t_llm_start) * 1000
                first_tts = False
            await ws.send_bytes(audio_chunk)

    response_text = "".join(full_response)
    orchestrator._update_history(text, response_text)

    t_end = time.perf_counter()

    await ws.send_json({
        "type": "turn_complete",
        "turn_id": turn_id,
        "metrics": {
            "stt_ms": 0,
            "llm_ttft_ms": round(ttft_ms, 1),
            "llm_total_ms": round((t_llm_end - t_llm_start) * 1000, 1),
            "tts_first_ms": round(tts_first_ms, 1),
            "e2e_ms": round((t_end - t_start) * 1000, 1),
        },
    })
