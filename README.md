<div align="center">

# Socratic AI Video Tutor

**An AI-powered avatar that teaches through questions, not answers.**

Real-time voice conversations with a lip-synced avatar that uses the Socratic method to guide students toward understanding — powered by dual-model LLM routing, streaming speech pipelines, and a pedagogical state machine.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#features) &bull; [Demo](#demo) &bull; [Quick Start](#quick-start) &bull; [Architecture](#architecture) &bull; [Configuration](#configuration) &bull; [Contributing](#contributing)

</div>

---

## Features

- **Socratic Tutoring Engine** — 7-state conversation FSM (OPENING &rarr; PROBE &rarr; SCAFFOLD &rarr; REDIRECT &rarr; CONFIRM &rarr; DEEPEN &rarr; CLOSE) that never gives direct answers
- **Dual-Model LLM Router** — Groq (Llama-3.3-70B) for fast acknowledgments, Claude for complex pedagogical scaffolding
- **Real-Time Streaming Pipeline** — Sub-second voice-to-voice: VAD &rarr; STT &rarr; LLM &rarr; TTS &rarr; Avatar
- **Lip-Synced AI Avatar** — Simli-powered video avatar with behavioral modes (listening, thinking, speaking)
- **Voice Activity Detection** — Silero VAD with energy-based fallback for accurate speech boundary detection
- **Sentence-Level Streaming** — Token accumulator emits complete sentences to TTS before the LLM finishes generating
- **Multiple Concepts** — Division by Zero, Photosynthesis, Gravity, Fractions, Water Cycle — each with misconception maps and scaffolding hints
- **Text Input Fallback** — Type responses when a microphone isn't available

## Demo

<!-- Add a GIF or screenshot of the tutor in action -->
> [Add demo GIF or screenshot here]

<details>
<summary>Example Conversation Flow</summary>

```
Avatar (OPENING):  "Hey! Have you ever tried dividing something by zero on a calculator?
                    What do you think happens — and why?"

Student:           "It gives an error"

Avatar (PROBE):    "Right! But why do you think the calculator refuses?
                    What would the answer even look like if it tried?"

Student:           "I don't know... infinity?"

Avatar (SCAFFOLD): "Interesting thought! Let's test it — if 6 ÷ 2 = 3, that means 3 × 2 = 6.
                    So if 6 ÷ 0 = something, what times 0 would need to equal 6?"

Student:           "Oh... nothing times zero is six. That's impossible!"

Avatar (CONFIRM):  "Exactly! So what does that tell us about dividing by zero?"
```

</details>

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys for: [AssemblyAI](https://www.assemblyai.com/), [Groq](https://groq.com/), [Anthropic](https://www.anthropic.com/), [ElevenLabs](https://elevenlabs.io/), [Simli](https://www.simli.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/rohanthomas1202/socratic-avatar.git
cd socratic-avatar

# Configure environment variables
cp .env.example .env
# Edit .env and add your API keys

# Install all dependencies
make install
```

### Running

```bash
# Start both server and client
make dev
```

Open [http://localhost:8060](http://localhost:8060) in your browser, select a concept, and start a session.

<details>
<summary>Manual startup (without Make)</summary>

```bash
# Terminal 1 — Server
cd server && pip install -e ".[dev]"
uvicorn main:app --reload --port 8050

# Terminal 2 — Client
cd client && npm install
npm run dev
```

</details>

<details>
<summary>Docker</summary>

```bash
docker-compose up
```

</details>

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Client (Next.js 14)                                            │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐                │
│  │ AudioCap │  │ TutorSession │  │ AvatarView │                │
│  │ (PCM16)  │  │  (Controls)  │  │  (Simli)   │                │
│  └────┬─────┘  └──────────────┘  └─────▲──────┘                │
│       │            WebSocket            │                       │
├───────┼─────────────────────────────────┼───────────────────────┤
│       ▼                                 │                       │
│  Server (FastAPI)                       │                       │
│  ┌─────┐   ┌─────┐   ┌──────────┐   ┌──┴──┐   ┌────────────┐  │
│  │ VAD │──▶│ STT │──▶│ Socratic │──▶│ LLM │──▶│  Sentence   │  │
│  │     │   │(Asm)│   │  State   │   │Route│   │  Chunker    │  │
│  └─────┘   └─────┘   │ Machine  │   │     │   └──────┬─────┘  │
│                       └──────────┘   └─────┘          │        │
│                                                       ▼        │
│                                                   ┌───────┐    │
│                                                   │  TTS  │    │
│                                                   │(11Labs)│   │
│                                                   └───┬───┘    │
│                                                       │ audio  │
└───────────────────────────────────────────────────────┼────────┘
                                                        ▼
                                                   Browser Audio
                                                   + Avatar Sync
```

### Pipeline Flow

| Stage | Service | Latency Target |
|-------|---------|----------------|
| Voice Activity Detection | Silero VAD | < 50ms |
| Speech-to-Text | AssemblyAI | < 300ms |
| LLM (time-to-first-token) | Groq / Claude | < 250ms |
| Text-to-Speech (first byte) | ElevenLabs v2 | < 200ms |
| Avatar Rendering | Simli WebRTC | < 130ms |
| **End-to-End** | **Full pipeline** | **< 1000ms** |

### Socratic State Machine

```
OPENING ──▶ PROBE ──▶ SCAFFOLD ──▶ CONFIRM ──▶ DEEPEN ──▶ CLOSE
                 │         ▲
                 ▼         │
              REDIRECT ────┘
```

Each state has tailored system prompts that enforce Socratic questioning — the tutor never lectures or gives direct answers.

### Dual-Model Routing

| State | Model | Rationale |
|-------|-------|-----------|
| OPENING, CONFIRM, CLOSE | Groq (Llama-3.3-70B) | Speed-optimized, simpler responses |
| PROBE, SCAFFOLD, REDIRECT, DEEPEN | Claude | Quality-optimized, nuanced pedagogy |

## Project Structure

```
socratic-avatar/
├── server/                     # Python FastAPI backend
│   ├── main.py                 # WebSocket endpoints
│   ├── config.py               # Pydantic settings
│   ├── pipeline/
│   │   ├── orchestrator.py     # Turn lifecycle coordinator
│   │   ├── vad.py              # Voice activity detection
│   │   ├── stt.py              # AssemblyAI streaming STT
│   │   ├── llm_router.py       # Dual-model routing logic
│   │   ├── llm_fast.py         # Groq client
│   │   ├── llm_quality.py      # Claude client
│   │   ├── sentence_chunker.py # Token → sentence boundaries
│   │   └── tts.py              # ElevenLabs streaming TTS
│   └── socratic/
│       ├── state_machine.py    # 7-state conversation FSM
│       ├── prompts.py          # State-specific system prompts
│       ├── concepts.py         # Concept definitions & hints
│       └── classifier.py       # Response categorization
│
├── client/                     # Next.js 14 frontend
│   ├── app/                    # App router pages
│   ├── components/
│   │   ├── TutorSession.tsx    # Main session orchestrator
│   │   ├── AvatarView.tsx      # Simli avatar embed
│   │   ├── AudioCapture.tsx    # Mic → PCM16 → WebSocket
│   │   └── SessionControls.tsx # Concept selector & controls
│   ├── hooks/
│   │   ├── useWebSocket.ts     # WebSocket connection
│   │   ├── useAudioStream.ts   # Mic capture & encoding
│   │   └── useAudioPlayback.ts # TTS audio playback
│   └── lib/
│       ├── simli.ts            # Simli SDK wrapper
│       └── types.ts            # Shared TypeScript types
│
├── tests/                      # Unit, integration & latency tests
├── benchmarks/                 # Performance benchmarking suite
├── Makefile                    # dev, test, bench, clean targets
├── docker-compose.yml          # Local containerized setup
└── .env.example                # API key template
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
# Speech-to-Text
ASSEMBLYAI_API_KEY=your_key_here

# LLM — Fast Path
GROQ_API_KEY=your_key_here

# LLM — Quality Path
ANTHROPIC_API_KEY=your_key_here

# Text-to-Speech
ELEVENLABS_API_KEY=your_key_here

# Avatar Rendering
SIMLI_API_KEY=your_key_here
```

### Server Settings

Server configuration is managed via Pydantic settings in `server/config.py`. Key defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `SERVER_PORT` | `8050` | FastAPI server port |
| `CLIENT_PORT` | `8060` | Next.js dev server port |
| Groq Model | `llama-3.3-70b-versatile` | Fast-path LLM |
| Claude Model | `claude-sonnet-4-6` | Quality-path LLM |
| TTS Voice | `eleven_turbo_v2` | ElevenLabs model |

## WebSocket Protocol

### Client &rarr; Server

| Type | Message | Description |
|------|---------|-------------|
| Binary | PCM16 chunks | 16kHz mono audio from microphone |
| JSON | `session_start` | Begin a new tutoring session |
| JSON | `text_input` | Send typed text instead of voice |
| JSON | `reset` | Reset conversation state |

### Server &rarr; Client

| Type | Message | Description |
|------|---------|-------------|
| Binary | PCM16 chunks | TTS audio for playback |
| JSON | `transcript` | Finalized STT transcript |
| JSON | `token` | Streaming LLM token |
| JSON | `turn_complete` | End of tutor response |
| JSON | `speech_started` / `speech_ended` | VAD events |

## Development

```bash
# Run tests
make test

# Run benchmarks
make bench

# Clean build artifacts
make clean
```

### Adding a New Concept

1. Add the concept definition in `server/socratic/concepts.py` with key ideas, misconceptions, diagnostic questions, and scaffolding hints
2. The concept automatically appears in the frontend dropdown

## Roadmap

- [x] Core streaming pipeline (VAD &rarr; STT &rarr; LLM &rarr; TTS)
- [x] Next.js frontend with mic capture & audio playback
- [x] Simli avatar with lip-sync & behavioral modes
- [x] Socratic state machine & dual-model routing
- [ ] Per-stage latency instrumentation & real-time dashboard
- [ ] Cost-per-turn tracking
- [ ] Benchmark framework with latency regression tests
- [ ] LLM-as-judge Socratic quality evaluation
- [ ] Full documentation & architecture deep-dive

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Make your changes and add tests
4. Run `make test` to verify everything passes
5. Commit with a descriptive message
6. Open a Pull Request

Please ensure your code:
- Passes all existing tests
- Includes tests for new functionality
- Follows the existing code style

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Credits

Built by [Rohan Thomas](https://github.com/rohanthomas1202)

### Powered By

| Service | Role |
|---------|------|
| [AssemblyAI](https://www.assemblyai.com/) | Speech-to-Text |
| [Groq](https://groq.com/) | Fast LLM inference |
| [Anthropic Claude](https://www.anthropic.com/) | Quality LLM responses |
| [ElevenLabs](https://elevenlabs.io/) | Text-to-Speech |
| [Simli](https://www.simli.com/) | Avatar rendering & lip-sync |
