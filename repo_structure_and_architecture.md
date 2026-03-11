# Repository Structure & System Architecture

## GitHub Repository Structure

```
socratic-tutor/
│
├── README.md                          # One-command setup, architecture overview, demo link
├── DECISION_LOG.md                    # What was tried, what worked, what didn't, WHY
├── .env.example                       # Template for API keys (Deepgram, Groq, OpenAI, ElevenLabs, Simli)
├── .gitignore
├── docker-compose.yml                 # One-command local setup
├── Makefile                           # make dev, make test, make bench, make demo
│
├── docs/
│   ├── architecture.md                # System architecture deep-dive
│   ├── latency-report.md              # Per-stage latency analysis with charts
│   ├── pipeline-comparison.md         # Config A vs B vs C experiment results
│   ├── socratic-evaluation.md         # Socratic quality scoring methodology + results
│   └── cost-analysis.md               # Cost-per-tutoring-minute breakdown
│
├── server/                            # Python orchestrator (FastAPI + asyncio)
│   ├── pyproject.toml                 # Dependencies (fastapi, uvicorn, websockets, numpy)
│   ├── main.py                        # FastAPI app entry, WebSocket endpoints
│   │
│   ├── pipeline/                      # Core streaming pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py            # Turn lifecycle: coordinates all stages
│   │   ├── vad.py                     # Silero VAD wrapper — voice activity detection
│   │   ├── stt.py                     # Deepgram Nova-2 streaming client
│   │   ├── llm_router.py             # Query classifier + model routing logic
│   │   ├── llm_fast.py               # Groq Llama-3.3-70B streaming client
│   │   ├── llm_quality.py            # GPT-4o-mini streaming client
│   │   ├── sentence_chunker.py       # Token accumulator → sentence boundary detection
│   │   ├── tts.py                     # ElevenLabs v2 / Cartesia streaming client
│   │   └── avatar.py                  # Simli audio → video streaming bridge
│   │
│   ├── socratic/                      # Socratic tutoring engine
│   │   ├── __init__.py
│   │   ├── state_machine.py           # OPENING→PROBE→SCAFFOLD→REDIRECT→CONFIRM→DEEPEN→CLOSE
│   │   ├── prompts.py                 # State-specific system prompts
│   │   ├── concepts.py                # Concept definitions (division by zero, photosynthesis, etc.)
│   │   └── classifier.py             # Rule-based query classifier (ack vs scaffold vs redirect)
│   │
│   ├── instrumentation/               # Latency tracking & metrics
│   │   ├── __init__.py
│   │   ├── timer.py                   # Per-stage timestamp collection
│   │   ├── metrics.py                 # Aggregation: mean, p50, p95, p99, variance
│   │   ├── cost_tracker.py            # Per-turn API cost calculation
│   │   └── logger.py                  # JSON log writer for per-turn metrics
│   │
│   └── config.py                      # Pipeline configuration (provider selection, latency budgets)
│
├── client/                            # Next.js 14 frontend
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   │
│   ├── app/
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Main tutor page
│   │   └── globals.css
│   │
│   ├── components/
│   │   ├── TutorSession.tsx           # Main session container — mic + avatar + dashboard
│   │   ├── AvatarView.tsx             # Simli video embed + behavioral mode controller
│   │   ├── AudioCapture.tsx           # Browser mic capture → WebSocket streaming
│   │   ├── LatencyDashboard.tsx       # Real-time per-stage latency overlay
│   │   └── SessionControls.tsx        # Start/stop, concept selector, settings
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts            # WebSocket connection to orchestrator
│   │   ├── useAudioStream.ts          # Mic capture + VAD integration
│   │   └── useLatencyMetrics.ts       # Receives + displays per-turn metrics
│   │
│   └── lib/
│       ├── simli.ts                   # Simli SDK wrapper
│       └── types.ts                   # Shared TypeScript types
│
├── tests/
│   ├── conftest.py                    # Shared fixtures (test audio samples, mock configs)
│   │
│   ├── unit/
│   │   ├── test_sentence_chunker.py   # Sentence boundary detection correctness
│   │   ├── test_state_machine.py      # Socratic state transitions
│   │   ├── test_llm_router.py         # Query classification routing decisions
│   │   ├── test_metrics.py            # Aggregation math (mean, p95, etc.)
│   │   └── test_cost_tracker.py       # Cost calculation accuracy
│   │
│   ├── integration/
│   │   ├── test_stt_pipeline.py       # Audio → Deepgram → transcript
│   │   ├── test_llm_streaming.py      # Prompt → Groq/GPT-4o-mini → streaming tokens
│   │   ├── test_tts_streaming.py      # Text → ElevenLabs → audio chunks
│   │   └── test_full_pipeline.py      # End-to-end: audio in → avatar audio out
│   │
│   └── latency/                       # Latency regression tests
│       ├── test_stt_budget.py         # STT p95 < 300ms
│       ├── test_llm_budget.py         # LLM TTFT p95 < 250ms
│       ├── test_tts_budget.py         # TTS first byte p95 < 200ms
│       └── test_e2e_budget.py         # E2E p95 < 1000ms
│
├── benchmarks/
│   ├── run_benchmark.py               # Run N conversations, collect latency stats
│   ├── compare_configs.py             # Side-by-side pipeline config comparison
│   ├── evaluate_socratic.py           # LLM-as-judge Socratic quality scorer
│   └── results/                       # Benchmark output (JSON + charts)
│       ├── .gitkeep
│       └── sample_results.json        # Example benchmark output
│
├── fixtures/                          # Test data
│   ├── audio_samples/                 # Short .wav files for STT testing
│   │   └── .gitkeep
│   └── conversation_transcripts/      # Sample conversations for Socratic evaluation
│       └── division_by_zero.json
│
└── scripts/
    ├── setup.sh                       # Install dependencies, check API keys
    └── record_demo.sh                 # Helper: screen record + latency overlay
```

---

## Key Repo Design Decisions

1. **`server/` and `client/` are siblings, not nested** — clean separation, independent dependency management, easy for reviewers to navigate

2. **`pipeline/` has one file per stage** — every stage is independently testable and swappable (swap `llm_fast.py` from Groq to Cerebras by changing one file)

3. **`socratic/` is its own module** — signals that educational quality is a first-class concern, not buried inside LLM prompts

4. **`tests/latency/` is a dedicated directory** — latency regression tests are separate from functional tests, making the benchmarking discipline visible to reviewers

5. **`benchmarks/` with `results/`** — shows experimental methodology; `compare_configs.py` proves you tested multiple pipeline configurations

6. **`DECISION_LOG.md` at root** — immediately visible, signals intellectual honesty and engineering rigor

7. **`Makefile` with `make dev`, `make test`, `make bench`** — one-command workflows for reviewers to reproduce everything

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT (Next.js 14)                               │
│                                                                             │
│  ┌──────────────┐    ┌───────────────────┐    ┌──────────────────────────┐  │
│  │ AudioCapture  │    │   AvatarView      │    │  LatencyDashboard       │  │
│  │              │    │   (Simli SDK)      │    │                          │  │
│  │ getUserMedia │    │                    │    │  Turn 7    E2E: 487ms   │  │
│  │ → PCM16 buf  │    │  ┌──────────────┐ │    │  ├─ STT:     142ms     │  │
│  │ → VAD detect │    │  │  Video Feed  │ │    │  ├─ LLM:     118ms     │  │
│  └──────┬───────┘    │  │  (WebRTC)    │ │    │  ├─ TTS:     139ms     │  │
│         │            │  └──────────────┘ │    │  ├─ Avatar:   88ms     │  │
│         │            │                    │    │  └─ p95:     623ms     │  │
│         │            │  Modes:            │    │                          │  │
│         │            │  • Listening       │    │  Socratic State: SCAFFOLD│  │
│         │            │  • Thinking        │    │  Model: GPT-4o-mini      │  │
│         │            │  • Speaking        │    │  Cost/turn: $0.004      │  │
│         │            └───────▲────────────┘    └──────────▲───────────────┘  │
│         │                    │                            │                   │
└─────────┼────────────────────┼────────────────────────────┼──────────────────┘
          │                    │                            │
          │ WS: audio chunks   │ WebRTC: lip-synced video   │ WS: metrics JSON
          │                    │                            │
          ▼                    │                            │
┌─────────────────────────────┴────────────────────────────┴──────────────────┐
│                         SERVER (FastAPI + asyncio)                           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      ORCHESTRATOR (orchestrator.py)                  │    │
│  │                                                                     │    │
│  │   Manages turn lifecycle:                                           │    │
│  │   1. Receive audio chunks from client                               │    │
│  │   2. Feed to VAD → detect speech end                                │    │
│  │   3. Stream to STT → get transcript                                 │    │
│  │   4. Classify → route to LLM                                        │    │
│  │   5. Stream LLM tokens → chunk sentences → stream TTS               │    │
│  │   6. Stream TTS audio → Simli avatar                                │    │
│  │   7. Emit per-stage metrics                                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ════════════════════ STREAMING PIPELINE ════════════════════               │
│                                                                             │
│  Audio In ─┐                                                                │
│            ▼                                                                │
│  ┌──────────────┐   ┌──────────────────┐   ┌────────────────────────┐      │
│  │   VAD        │──▶│  STT             │──▶│  QUERY CLASSIFIER      │      │
│  │   (Silero)   │   │  (Deepgram)      │   │  (rule-based)          │      │
│  │              │   │                  │   │                        │      │
│  │  Detects     │   │  Streaming WS    │   │  Categories:           │      │
│  │  speech end  │   │  → partial txts  │   │  • ACK (short)         │      │
│  │  ~30ms       │   │  → final txt     │   │  • SCAFFOLD (complex)  │      │
│  │              │   │  ~150ms          │   │  • REDIRECT (wrong)    │      │
│  │  t0 ────────────▶│  t1 ────────────────▶│  <20ms                 │      │
│  └──────────────┘   └──────────────────┘   └───────────┬────────────┘      │
│                                                         │                   │
│                                              ┌──────────▼──────────┐        │
│                                              │    LLM ROUTER       │        │
│                                              │                     │        │
│                                              │  ACK ──────┐        │        │
│                                              │            ▼        │        │
│                                              │  ┌──────────────┐   │        │
│                                              │  │ GROQ         │   │        │
│                                              │  │ Llama-3.3    │   │        │
│                                              │  │ ~80ms TTFT   │   │        │
│                                              │  └──────┬───────┘   │        │
│                                              │         │           │        │
│                                              │  SCAFFOLD/REDIRECT  │        │
│                                              │            ▼        │        │
│                                              │  ┌──────────────┐   │        │
│                                              │  │ GPT-4o-mini  │   │        │
│                                              │  │ ~180ms TTFT  │   │        │
│                                              │  └──────┬───────┘   │        │
│                                              │         │           │        │
│                                              │  t2 ◄───┴───────┘   │        │
│                                              └──────────┬──────────┘        │
│                                                         │                   │
│                                                         │ streaming tokens  │
│                                                         ▼                   │
│                                              ┌─────────────────────┐        │
│                                              │ SENTENCE CHUNKER    │        │
│                                              │                     │        │
│                                              │ Accumulate tokens   │        │
│                                              │ until . ? ! detected│        │
│                                              │ Then emit sentence  │        │
│                                              │ ~50ms added latency │        │
│                                              └──────────┬──────────┘        │
│                                                         │                   │
│                                                         │ complete sentences│
│                                                         ▼                   │
│                                              ┌─────────────────────┐        │
│                                              │ STREAMING TTS       │        │
│                                              │ (ElevenLabs v2)     │        │
│                                              │                     │        │
│                                              │ Sentence → PCM16    │        │
│                                              │ audio chunks        │        │
│                                              │ ~120ms first byte   │        │
│                                              │ t3 ─────────────────│        │
│                                              └──────────┬──────────┘        │
│                                                         │                   │
│                                                         │ audio chunks      │
│                                                         ▼                   │
│                                              ┌─────────────────────┐        │
│                                              │ SIMLI AVATAR        │        │
│                                              │                     │        │
│                                              │ Audio → lip-synced  │        │
│                                              │ video frames        │        │
│                                              │ → WebRTC to client  │        │
│                                              │ ~80ms render        │        │
│                                              │ t4 ─────────────────│        │
│                                              └─────────────────────┘        │
│                                                                             │
│  ════════════════════ PARALLEL SYSTEMS ═══════════════════                  │
│                                                                             │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │  LATENCY INSTRUMENTER   │  │  SOCRATIC STATE MACHINE                 │  │
│  │                         │  │                                         │  │
│  │  Captures t0→t1→t2→    │  │  Current state determines:              │  │
│  │  t3→t4 at every stage   │  │  • Which system prompt to use           │  │
│  │                         │  │  • How to classify the response type     │  │
│  │  Per turn emits:        │  │  • Whether to transition states          │  │
│  │  {                      │  │                                         │  │
│  │    turn_id: 7,          │  │  ┌────────┐   ┌───────┐   ┌─────────┐ │  │
│  │    stt_ms: 142,         │  │  │OPENING │──▶│ PROBE │──▶│SCAFFOLD │ │  │
│  │    llm_ttft_ms: 118,    │  │  └────────┘   └───────┘   └────┬────┘ │  │
│  │    tts_first_ms: 139,   │  │                                 │      │  │
│  │    avatar_ms: 88,       │  │       ┌─────────┐◄──────────────┘      │  │
│  │    e2e_ms: 487,         │  │       │REDIRECT │  (wrong answer)      │  │
│  │    model: "groq",       │  │       └────┬────┘                      │  │
│  │    state: "SCAFFOLD",   │  │            │                           │  │
│  │    cost_usd: 0.004      │  │       ┌────▼────┐   ┌──────┐          │  │
│  │  }                      │  │       │ CONFIRM │──▶│DEEPEN│──▶CLOSE  │  │
│  │                         │  │       └─────────┘   └──────┘          │  │
│  │  → JSON log file        │  │                                         │  │
│  │  → WebSocket to client  │  │  Tracks: concepts covered, student      │  │
│  │    (dashboard)          │  │  understanding level, question history   │  │
│  └─────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                        ════ DATA FLOW SUMMARY ════

  Student speaks → [30ms VAD] → [150ms STT] → [<20ms classify] → [80-180ms LLM]
                 → [50ms chunk] → [120ms TTS] → [80ms avatar] → Student sees/hears

  Target E2E: <500ms (ideal) / <1000ms (required)
  Latency hiding: 200ms "thinking" animation masks pipeline processing
```

---

## Transport Layer Detail

```
┌────────────┐         ┌────────────────┐         ┌──────────────┐
│   Browser   │◄──WS──▶│  FastAPI Server │◄──WS──▶│   Deepgram   │
│            │         │                │◄─HTTP──▶│   Groq       │
│  Mic audio ├──WS──▶  │                │◄─HTTP──▶│   OpenAI     │
│            │         │                │◄──WS──▶│   ElevenLabs  │
│  Avatar    │◄─WebRTC─│                │◄──WS──▶│   Simli       │
│  video     │         │                │         │              │
│            │         │                │         │              │
│  Metrics   │◄──WS────│  Instrumenter  │         │              │
│  dashboard │         │                │         │              │
└────────────┘         └────────────────┘         └──────────────┘

Protocols:
  • Client ↔ Server:  WebSocket (audio + metrics), WebRTC (avatar video)
  • Server ↔ Deepgram: WebSocket (streaming STT)
  • Server ↔ Groq:     HTTPS streaming (SSE)
  • Server ↔ OpenAI:   HTTPS streaming (SSE)
  • Server ↔ ElevenLabs: WebSocket (streaming TTS)
  • Server ↔ Simli:    WebSocket (audio in, WebRTC signaling)
```

---

## Latency Budget Allocation

```
┌─────────────────────────────────────────────────────────┐
│              LATENCY BUDGET (Target: <500ms)             │
│                                                         │
│  Stage              Ideal    Max     Notes               │
│  ─────────────────  ──────   ─────   ──────────────────  │
│  VAD detection       30ms    50ms    Local, Silero       │
│  STT (Deepgram)    150ms   300ms    Streaming, final    │
│  Query classify      <5ms    20ms    Rule-based, local   │
│  LLM TTFT           80ms   200ms    Groq fast / GPT-4o  │
│  Sentence chunk     50ms   100ms    Wait for boundary   │
│  TTS first byte    120ms   200ms    ElevenLabs stream   │
│  Avatar render      80ms   130ms    Simli WebRTC        │
│  ─────────────────  ──────   ─────                       │
│  TOTAL             ~515ms  1000ms                        │
│                                                         │
│  Note: Stages overlap via streaming.                    │
│  Actual E2E < sum of stages because LLM→TTS→Avatar     │
│  pipeline streams continuously.                          │
│                                                         │
│  With streaming overlap, real E2E ≈ 400-600ms           │
│  With thinking animation, perceived E2E ≈ 200-400ms    │
└─────────────────────────────────────────────────────────┘
```
