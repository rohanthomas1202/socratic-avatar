import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from pipeline.orchestrator import PipelineOrchestrator

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

                    # Get buffered audio and process the turn
                    buffered_audio = orchestrator.vad.get_buffered_audio()
                    if buffered_audio:
                        async for event in orchestrator.process_turn_streaming(buffered_audio):
                            await ws.send_json(event)

                    orchestrator.vad.reset()

            elif "text" in message and message["text"]:
                data = json.loads(message["text"])
                msg_type = data.get("type", "")

                if msg_type == "text_input":
                    # Direct text input (for testing without mic)
                    text = data.get("text", "")
                    if text:
                        # Create a fake turn with just text → LLM
                        orchestrator.session.turn_count += 1
                        turn_id = orchestrator.session.turn_count

                        await ws.send_json({
                            "type": "transcript",
                            "turn_id": turn_id,
                            "text": text,
                            "stt_ms": 0,
                        })

                        full_response = []
                        async for token in orchestrator.llm.generate_stream(
                            user_message=text,
                            conversation_history=orchestrator.session.conversation_history,
                        ):
                            full_response.append(token)
                            await ws.send_json({
                                "type": "token",
                                "turn_id": turn_id,
                                "text": token,
                            })

                        response_text = "".join(full_response)
                        orchestrator.session.conversation_history.append(
                            {"role": "user", "content": text}
                        )
                        orchestrator.session.conversation_history.append(
                            {"role": "assistant", "content": response_text}
                        )

                        await ws.send_json({
                            "type": "turn_complete",
                            "turn_id": turn_id,
                            "metrics": {"stt_ms": 0, "llm_ttft_ms": 0, "e2e_ms": 0},
                        })

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
