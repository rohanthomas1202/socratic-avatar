import asyncio
import json
import logging

import httpx
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


@app.post("/api/simli/token")
async def simli_token():
    """Generate a Simli session token and ICE servers (keeps API key server-side)."""
    if not settings.simli_api_key:
        return {"error": "SIMLI_API_KEY not configured"}, 500

    async with httpx.AsyncClient() as client:
        # Fetch session token and ICE servers in parallel
        token_req = client.post(
            "https://api.simli.ai/startAudioToVideoSession",
            json={
                "apiKey": settings.simli_api_key,
                "faceId": settings.simli_face_id,
                "handleSilence": True,
                "maxSessionLength": 3600,
                "maxIdleTime": 300,
            },
        )
        ice_req = client.get(
            "https://api.simli.ai/getIceServers",
            params={"apiKey": settings.simli_api_key},
        )

        token_resp, ice_resp = await asyncio.gather(token_req, ice_req)
        token_resp.raise_for_status()

        result = token_resp.json()

        # Attach ICE servers if available
        if ice_resp.status_code == 200:
            result["ice_servers"] = ice_resp.json()
        else:
            logger.warning(f"Failed to get ICE servers: {ice_resp.status_code}")

        return result


@app.websocket("/ws/session")
async def websocket_session(ws: WebSocket):
    """WebSocket endpoint for a tutoring session.

    Protocol:
    - Client sends: binary audio chunks (PCM16, 16kHz, mono)
                    OR JSON text messages for control
    - Server sends: JSON messages with transcripts, tokens, metrics, socratic_state
                    Binary messages with TTS audio chunks
    """
    await ws.accept()

    concept_id = None
    orchestrator = None

    logger.info("WebSocket session connected")

    try:
        while True:
            message = await ws.receive()

            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]

                if orchestrator is None:
                    orchestrator = PipelineOrchestrator(concept_id=concept_id)

                vad_result = orchestrator.process_audio_chunk(audio_bytes)

                if vad_result["speech_started"]:
                    await ws.send_json({"type": "speech_started"})

                if vad_result["speech_ended"]:
                    await ws.send_json({"type": "speech_ended"})

                    buffered_audio = orchestrator.vad.get_buffered_audio()
                    if buffered_audio:
                        async for event in orchestrator.process_turn_streaming(buffered_audio):
                            if event["type"] == "audio":
                                await ws.send_bytes(event["data"])
                            else:
                                await ws.send_json(event)

                    orchestrator.vad.reset()

            elif "text" in message and message["text"]:
                data = json.loads(message["text"])
                msg_type = data.get("type", "")

                if msg_type == "session_start":
                    concept_id = data.get("concept_id", "division_by_zero")
                    orchestrator = PipelineOrchestrator(concept_id=concept_id)
                    logger.info(f"Session started with concept: {concept_id}")
                    await ws.send_json({
                        "type": "session_started",
                        "concept_id": concept_id,
                        "socratic_state": orchestrator.current_state.value,
                    })

                elif msg_type == "text_input":
                    text = data.get("text", "")
                    if text:
                        if orchestrator is None:
                            orchestrator = PipelineOrchestrator(concept_id=concept_id)

                        async for event in orchestrator.process_text_turn_streaming(text):
                            if event["type"] == "audio":
                                await ws.send_bytes(event["data"])
                            else:
                                await ws.send_json(event)

                elif msg_type == "reset":
                    if orchestrator:
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
