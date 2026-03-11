# Socratic AI Video Tutor — Implementation Phases

> **Git Policy**: NEVER commit or push to git automatically. After each phase, a suggested commit message is provided. The user decides when and how to commit.
> **Phase Gate**: Do NOT proceed to the next phase until the current phase is verified, tested, and marked DONE.

---

## Phase 1: Project Scaffolding & Configuration
**Status**: [x] DONE
**Goal**: Complete project structure, all dependencies installed, config system working.

### Tasks
- [ ] Create full directory structure (server/, client/, tests/, docs/, benchmarks/, fixtures/, scripts/)
- [ ] `server/pyproject.toml` — FastAPI, uvicorn, websockets, numpy, httpx, python-dotenv, pydantic-settings
- [ ] `client/package.json` — Next.js 14, React, TypeScript
- [ ] `.env.example` — All API key placeholders
- [ ] `server/config.py` — Pydantic settings loading from `.env`
- [ ] `server/main.py` — FastAPI app with health check endpoint
- [ ] `Makefile` — `make dev`, `make test`, `make install`
- [ ] `docker-compose.yml` — Local setup
- [ ] `.gitignore` — Python + Node
- [ ] `tests/conftest.py` — Shared fixtures
- [ ] All `__init__.py` files
- [ ] `client/app/layout.tsx`, `client/app/page.tsx`, `client/app/globals.css`

### How to Test
```bash
# 1. Install server dependencies
cd server && pip install -e .

# 2. Install client dependencies
cd client && npm install

# 3. Start server (in one terminal)
cd server && uvicorn main:app --reload --port 8050

# 4. Check health endpoint
curl http://localhost:8050/health
# Expected: {"status": "ok"}

# 5. Run tests (should be 0 tests, 0 errors)
pytest tests/ -v

# 6. Build client
cd client && npm run build
# Expected: Build succeeds with no errors

# 7. Start client (in another terminal)
cd client && npm run dev
# Expected: Page loads at http://localhost:8060
```

### Suggested Commit Message
```
feat: scaffold project structure with FastAPI server, Next.js client, config, and Makefile
```

---

## Phase 2: Server Pipeline — VAD + STT + Basic LLM
**Status**: [ ] NOT STARTED
**Goal**: Audio bytes → transcript → LLM text response (non-streaming, server-only).

### Tasks
- [ ] `server/pipeline/vad.py` — Silero VAD wrapper (detects speech end in audio buffer)
- [ ] `server/pipeline/stt.py` — Deepgram Nova-2 streaming WebSocket client
- [ ] `server/pipeline/llm_fast.py` — Groq Llama-3.3-70B streaming client (basic Socratic prompt)
- [ ] `server/pipeline/orchestrator.py` — Turn lifecycle coordinator (sequential)
- [ ] `server/main.py` — Add WebSocket endpoint `/ws/session`
- [ ] `tests/unit/test_vad.py` — Mock audio → detect speech
- [ ] `tests/unit/test_stt.py` — Mock → transcript

### How to Test
```bash
# 1. Run unit tests
pytest tests/unit/ -v
# Expected: All tests pass

# 2. Start server
cd server && uvicorn main:app --reload --port 8050

# 3. Test WebSocket manually (use websocat or a Python script)
# Send a .wav file through the /ws/session endpoint
# Expected: Receive LLM text response back

# 4. Verify Deepgram connection (requires DEEPGRAM_API_KEY in .env)
# Check server logs for "Deepgram connected" or similar

# 5. Verify Groq streaming (requires GROQ_API_KEY in .env)
# Check server logs for LLM response tokens

# 6. Ensure all previous tests still pass
pytest tests/ -v
```

### Suggested Commit Message
```
feat: add VAD, Deepgram STT, and Groq LLM pipeline with WebSocket endpoint
```

---

## Phase 3: Sentence Chunker + TTS + Streaming Pipeline
**Status**: [ ] NOT STARTED
**Goal**: LLM tokens stream → sentence chunker → TTS → audio bytes back. True streaming.

### Tasks
- [ ] `server/pipeline/sentence_chunker.py` — Token accumulator, emits on sentence boundary (. ? !)
- [ ] `server/pipeline/tts.py` — ElevenLabs v2 streaming WebSocket client
- [ ] `server/pipeline/llm_quality.py` — GPT-4o-mini streaming client (scaffold)
- [ ] Update `orchestrator.py` — Wire streaming: STT → LLM stream → chunker → TTS stream → WS audio out
- [ ] `tests/unit/test_sentence_chunker.py` — Sentence boundary detection tests
- [ ] `tests/integration/test_stt_pipeline.py` — Audio → Deepgram → transcript
- [ ] `tests/integration/test_llm_streaming.py` — Prompt → Groq → streaming tokens
- [ ] `tests/integration/test_tts_streaming.py` — Text → ElevenLabs → audio chunks

### How to Test
```bash
# 1. Run sentence chunker unit tests
pytest tests/unit/test_sentence_chunker.py -v
# Expected: All boundary detection tests pass

# 2. Run all unit tests
pytest tests/unit/ -v
# Expected: All pass

# 3. Run integration tests (requires API keys in .env)
pytest tests/integration/ -v
# Expected: STT, LLM, and TTS integration tests pass

# 4. Manual streaming test
# Start server: cd server && uvicorn main:app --reload --port 8050
# Send audio via WebSocket to /ws/session
# Expected: Receive PCM16 audio chunks back (not just text)
# Verify: First audio chunk arrives BEFORE LLM finishes generating (streaming works)

# 5. All tests pass
pytest tests/ -v
```

### Suggested Commit Message
```
feat: add sentence chunker, ElevenLabs TTS, and streaming pipeline wiring
```

---

## Phase 4: Frontend Foundation + Audio Capture
**Status**: [ ] NOT STARTED
**Goal**: Next.js app captures mic audio, sends via WebSocket, plays back TTS audio.

### Tasks
- [ ] `client/components/TutorSession.tsx` — Main session container
- [ ] `client/components/AudioCapture.tsx` — Browser mic → PCM16 → WebSocket
- [ ] `client/components/SessionControls.tsx` — Start/stop, concept selector
- [ ] `client/hooks/useWebSocket.ts` — WebSocket connection to server
- [ ] `client/hooks/useAudioStream.ts` — Mic capture + streaming
- [ ] `client/lib/types.ts` — Shared TypeScript types
- [ ] `client/app/page.tsx` — Wire up session UI
- [ ] Audio playback via Web Audio API

### How to Test
```bash
# 1. Build client (no TypeScript errors)
cd client && npm run build
# Expected: Build succeeds

# 2. Start both server and client
# Terminal 1: cd server && uvicorn main:app --reload --port 8050
# Terminal 2: cd client && npm run dev

# 3. Open http://localhost:8060 in browser
# Expected: Tutor session page loads

# 4. Click "Start Session"
# Expected: Browser requests microphone permission

# 5. Speak into microphone
# Expected: Browser console shows audio buffer sizes being captured

# 6. Check server terminal
# Expected: Server logs show WebSocket connection and incoming audio

# 7. Full audio loop test
# Speak → Wait → Hear TTS audio response through speakers
# (No avatar yet — just audio in/out)

# 8. All server tests still pass
pytest tests/ -v
```

### Suggested Commit Message
```
feat: add Next.js frontend with mic capture, WebSocket streaming, and audio playback
```

---

## Phase 5: Simli Avatar Integration
**Status**: [ ] NOT STARTED
**Goal**: Avatar renders lip-synced video from TTS audio. Behavioral modes working.

### Tasks
- [ ] `client/lib/simli.ts` — Simli SDK wrapper (init, audio feeding, WebRTC)
- [ ] `client/components/AvatarView.tsx` — Simli video embed + mode controller
- [ ] `server/pipeline/avatar.py` — Server-side Simli bridge (if needed)
- [ ] Avatar behavioral modes: listening, thinking, speaking
- [ ] Update `TutorSession.tsx` — Include AvatarView
- [ ] Thinking animation: ~200ms "thinking" pose before first audio

### How to Test
```bash
# 1. Build client
cd client && npm run build
# Expected: No TypeScript errors

# 2. Start server + client
# Terminal 1: cd server && uvicorn main:app --reload --port 8050
# Terminal 2: cd client && npm run dev

# 3. Open http://localhost:8060
# Expected: Avatar video element visible on page

# 4. Click "Start Session"
# Expected: Avatar enters "listening" mode (idle animation)

# 5. Speak into microphone
# Expected sequence:
#   a. Avatar stays in "listening" mode while you speak
#   b. After you stop, avatar enters "thinking" mode (~200ms)
#   c. Avatar transitions to "speaking" with lip-synced video
#   d. After response, avatar returns to "listening"

# 6. Check browser console
# Expected: No WebRTC/Simli errors

# 7. Visual check: Lip sync matches audio output

# 8. All server tests still pass
pytest tests/ -v
```

### Suggested Commit Message
```
feat: integrate Simli avatar with lip-sync, behavioral modes, and thinking animation
```

---

## Phase 6: Socratic State Machine + LLM Router
**Status**: [ ] NOT STARTED
**Goal**: Excellent Socratic tutoring. State machine drives prompts. Dual-model routing.

### Tasks
- [ ] `server/socratic/state_machine.py` — OPENING → PROBE → SCAFFOLD → REDIRECT → CONFIRM → DEEPEN → CLOSE
- [ ] `server/socratic/prompts.py` — State-specific system prompts
- [ ] `server/socratic/concepts.py` — Concept definitions (division by zero, photosynthesis)
- [ ] `server/socratic/classifier.py` — Rule-based query classifier (ACK vs SCAFFOLD vs REDIRECT)
- [ ] `server/pipeline/llm_router.py` — Routes to Groq (fast) or GPT-4o-mini (quality)
- [ ] Update orchestrator — Use state machine + router
- [ ] `tests/unit/test_state_machine.py` — State transition tests
- [ ] `tests/unit/test_llm_router.py` — Routing decision tests

### How to Test
```bash
# 1. Run state machine tests
pytest tests/unit/test_state_machine.py -v
# Expected: All state transitions correct

# 2. Run router tests
pytest tests/unit/test_llm_router.py -v
# Expected: Routing decisions correct

# 3. All tests pass
pytest tests/ -v

# 4. Manual Socratic conversation test (division by zero)
# Start server + client, open browser, start session
# Select "Division by Zero" concept
#
# Verify this conversation flow:
#   Turn 1: Avatar greets you (OPENING state)
#   Turn 2: Avatar asks diagnostic question (PROBE)
#   Turn 3: Answer correctly → Avatar asks "why?" (CONFIRM)
#   Turn 4: Answer incorrectly → Avatar asks revealing question (REDIRECT)
#   Turn 5: Avatar guides with questions (SCAFFOLD)
#   Turn 6: Avatar adds complexity (DEEPEN)
#   Turn 7: Avatar summarizes through questions (CLOSE)
#
# CRITICAL CHECK: The tutor NEVER gives a direct answer or lectures.
# Every response should end with a guiding question.

# 5. Verify model routing in server logs:
#   - Short acknowledgments → Groq (fast path)
#   - Complex scaffolding → GPT-4o-mini (quality path)
```

### Suggested Commit Message
```
feat: add Socratic state machine, query classifier, and dual-model LLM router
```

---

## Phase 7: Instrumentation + Latency Dashboard + Cost Tracking
**Status**: [ ] NOT STARTED
**Goal**: Full per-stage latency instrumentation. Real-time dashboard. Cost tracking.

### Tasks
- [ ] `server/instrumentation/timer.py` — Per-stage timestamp collection (t0→t1→t2→t3→t4)
- [ ] `server/instrumentation/metrics.py` — Aggregation: mean, p50, p95, p99, variance
- [ ] `server/instrumentation/cost_tracker.py` — Per-turn API cost calculation
- [ ] `server/instrumentation/logger.py` — JSON log writer for per-turn metrics
- [ ] `client/components/LatencyDashboard.tsx` — Real-time per-stage latency overlay
- [ ] `client/hooks/useLatencyMetrics.ts` — Receives metrics via WebSocket
- [ ] Update orchestrator — Emit metrics JSON after each turn
- [ ] `tests/unit/test_metrics.py` — Aggregation math tests
- [ ] `tests/unit/test_cost_tracker.py` — Cost calculation tests

### How to Test
```bash
# 1. Run metrics tests
pytest tests/unit/test_metrics.py -v
# Expected: Aggregation math correct (mean, p50, p95, p99, variance)

# 2. Run cost tracker tests
pytest tests/unit/test_cost_tracker.py -v
# Expected: Cost calculations accurate

# 3. All tests pass
pytest tests/ -v

# 4. Build client
cd client && npm run build
# Expected: No TypeScript errors

# 5. Start server + client, open browser
# Expected: Latency dashboard visible in UI

# 6. Have a conversation (3-5 turns)
# Dashboard should show per-turn breakdown:
#   ┌──────────────────────────────────┐
#   │ Turn N          E2E: XXXms       │
#   │ ├─ STT:          XXXms          │
#   │ ├─ LLM (TTFT):   XXXms          │
#   │ ├─ TTS (first):  XXXms          │
#   │ ├─ Avatar:        XXXms          │
#   │                                  │
#   │ Session avg:     XXXms           │
#   │ p95:             XXXms           │
#   │ Socratic State: SCAFFOLD         │
#   │ Model: groq / gpt-4o-mini       │
#   │ Cost/turn: $X.XXX               │
#   └──────────────────────────────────┘

# 7. Check for JSON log file on server
# Expected: metrics log file with per-turn JSON entries

# 8. Verify metrics accuracy
# Compare dashboard values with approximate manual timing
```

### Suggested Commit Message
```
feat: add per-stage latency instrumentation, real-time dashboard, and cost tracking
```

---

## Phase 8: Benchmarking, Full Test Suite & Documentation
**Status**: [ ] NOT STARTED
**Goal**: Complete benchmark framework, all tests pass, documentation written, demo-ready.

### Tasks
- [ ] `benchmarks/run_benchmark.py` — Run N conversations, collect latency stats
- [ ] `benchmarks/compare_configs.py` — Side-by-side pipeline config comparison
- [ ] `benchmarks/evaluate_socratic.py` — LLM-as-judge Socratic quality scorer
- [ ] `tests/latency/test_stt_budget.py` — STT p95 < 300ms
- [ ] `tests/latency/test_llm_budget.py` — LLM TTFT p95 < 250ms
- [ ] `tests/latency/test_tts_budget.py` — TTS first byte p95 < 200ms
- [ ] `tests/latency/test_e2e_budget.py` — E2E p95 < 1000ms
- [ ] `tests/integration/test_full_pipeline.py` — End-to-end integration test
- [ ] `docs/architecture.md` — System architecture deep-dive
- [ ] `docs/latency-report.md` — Per-stage latency analysis
- [ ] `docs/pipeline-comparison.md` — Config A vs B vs C results
- [ ] `docs/socratic-evaluation.md` — Quality scoring methodology + results
- [ ] `docs/cost-analysis.md` — Cost-per-tutoring-minute breakdown
- [ ] `DECISION_LOG.md` — What was tried, what worked, what didn't, WHY
- [ ] `README.md` — One-command setup, architecture overview, demo link
- [ ] `scripts/setup.sh` — Install dependencies, check API keys
- [ ] Update Makefile — `make bench`, `make demo`
- [ ] `fixtures/audio_samples/` — Test .wav files
- [ ] `fixtures/conversation_transcripts/division_by_zero.json` — Sample conversation

### How to Test
```bash
# 1. Run ALL tests
make test
# Expected: ALL tests pass (unit + integration + latency)

# 2. Run benchmarks
make bench
# Expected: Benchmark outputs to benchmarks/results/
# Check: benchmarks/results/sample_results.json exists

# 3. Verify latency budgets
pytest tests/latency/ -v
# Expected:
#   STT p95 < 300ms    ✓
#   LLM TTFT p95 < 250ms ✓
#   TTS first byte p95 < 200ms ✓
#   E2E p95 < 1000ms   ✓

# 4. Run Socratic evaluator
python benchmarks/evaluate_socratic.py
# Expected: Socratic quality scores > 7/10

# 5. Full E2E test
make dev
# Open http://localhost:8060
# Have a full conversation — everything works

# 6. Test setup script
bash scripts/setup.sh
# Expected: Checks for API keys, installs dependencies

# 7. Documentation check
# Verify all docs/*.md files exist and are complete
# Verify README.md has one-command setup instructions
# Verify DECISION_LOG.md documents key decisions

# 8. Client builds clean
cd client && npm run build
```

### Suggested Commit Message
```
feat: add benchmarking framework, latency regression tests, and full documentation
```

---

## Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project Scaffolding & Configuration | [x] DONE |
| 2 | Server Pipeline — VAD + STT + Basic LLM | [ ] NOT STARTED |
| 3 | Sentence Chunker + TTS + Streaming Pipeline | [ ] NOT STARTED |
| 4 | Frontend Foundation + Audio Capture | [ ] NOT STARTED |
| 5 | Simli Avatar Integration | [ ] NOT STARTED |
| 6 | Socratic State Machine + LLM Router | [ ] NOT STARTED |
| 7 | Instrumentation + Latency Dashboard + Cost Tracking | [ ] NOT STARTED |
| 8 | Benchmarking, Full Test Suite & Documentation | [ ] NOT STARTED |
