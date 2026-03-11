from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # API Keys
    assemblyai_api_key: str = Field(default="", description="AssemblyAI API key for STT")
    groq_api_key: str = Field(default="", description="Groq API key for fast LLM")
    anthropic_api_key: str = Field(default="", description="Anthropic API key for quality LLM (Claude)")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key for TTS")
    simli_api_key: str = Field(default="", description="Simli API key for avatar")

    # Server
    host: str = "0.0.0.0"
    port: int = 8050
    cors_origins: list[str] = ["http://localhost:8060"]

    # Pipeline latency budgets (ms)
    vad_budget_ms: int = 50
    stt_budget_ms: int = 300
    llm_budget_ms: int = 250
    tts_budget_ms: int = 200
    avatar_budget_ms: int = 130
    e2e_budget_ms: int = 1000

    # TTS
    tts_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs default voice
    tts_model_id: str = "eleven_turbo_v2"

    # LLM
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_model: str = "claude-sonnet-4-6"

    model_config = {
        "env_file": str(Path(__file__).parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
