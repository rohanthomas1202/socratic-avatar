# TOP 1% SUBMISSION STRATEGY: Live AI Video Tutor

## Chosen Project: A — Live AI Video Tutor / Low Latency Response

---

## STEP 1 — What Average Candidates Will Build

### The Generic Submission

Most candidates will follow the starter kit's Approach A (Collapsed Pipeline) almost verbatim:

**Common architecture:**
```
Student mic → OpenAI Realtime API (STT+LLM+TTS as black box) → Simli/HeyGen avatar → screen
```

**Obvious implementation choices:**
- OpenAI Realtime API for the entire middle pipeline (one WebSocket call handles STT + LLM + TTS)
- Simli or HeyGen Interactive Avatar for the video component
- Basic React frontend with a video element and a "start" button
- System prompt: "You are a Socratic tutor. Ask guiding questions instead of giving answers."
- Latency measured once at the end with `console.log(Date.now() - startTime)`
- README that says "run `npm start`" and a 2-minute screen recording

**Why these submissions feel generic:**

1. **Zero per-stage visibility.** The OpenAI Realtime API is a black box — you can't report STT latency, LLM TTFT, or TTS first byte independently. The evaluation requires per-stage breakdown. Automatic -10 if missing.

2. **No evidence of understanding.** The candidate plugged APIs together. A reviewer cannot distinguish "I understand streaming pipeline architecture" from "I followed a tutorial." The Technical Innovation category (15%) rewards demonstrating *deep understanding of bottlenecks in each stage*. API glue scores 0-7 points out of 15.

3. **Identical to every other candidate.** When 30% of submissions use OpenAI Realtime + Simli, reviewers see the same avatar, hear the same voice, and experience the same ~700ms latency. There is no separation.

4. **Socratic method is an afterthought.** Generic system prompt produces generic tutoring. The tutor says "That's a great question! Let me ask you..." in every response. No adaptation, no scaffolding progression, no concept tracking. Educational Quality is 25% of the score — equal to latency.

5. **No benchmarking framework.** A single `console.log` timestamp is not a benchmarking framework. No variance analysis, no per-stage breakdown, no comparison across configurations. The submission checklist explicitly requires "per-stage latency breakdown reported."

6. **Avatar sits there doing nothing while waiting.** No idle animations, no listening cues, no "thinking" behavior. The avatar is a static face that suddenly starts talking. It feels like a disconnected overlay, which is exactly what the rubric penalizes.

### The Mediocre Score

A typical submission following this pattern will score:
- Latency: 12-17/25 (acceptable tier, ~1-2s E2E, no streaming innovation)
- Video: 8-10/15 (basic avatar, some lip-sync, limited expressiveness)
- Educational Quality: 13-17/25 (some Socratic, but frequently lectures)
- Technical Innovation: 8-10/15 (standard architecture, no novel optimization)
- Implementation: 5-6/10 (basic structure, few tests)
- Documentation: 5-6/10 (basic latency reporting, limited analysis)
- **Total: ~56-66/100 — "Acceptable" to low "Good"**
- Plus automatic deductions risk if latency >3s or no per-stage breakdown

---

## STEP 2 — What a Top 1% Submission Looks Like

### The Core Insight

The top 1% submission is not a better version of the average submission. It's a **fundamentally different approach** that treats the project as a *systems engineering challenge with measurable optimization*, not an API integration exercise.

The key differentiator: **the candidate demonstrates they understand WHY each component takes the time it does, and shows evidence of experimenting to reduce it.**

### The Architecture: Composable Pipeline with Full Instrumentation

Instead of a black-box collapsed pipeline, build a **composable pipeline (Approach B)** where every stage is:
1. Independently measurable
2. Independently swappable
3. Streaming into the next stage in real-time

```
Student mic
  → [VAD: Silero]
  → [Streaming STT: Deepgram Nova-2]
  → [Query Classifier: lightweight, <20ms]
  → [LLM Router]
      → Short response path: Groq Llama-3.3-70B (~80ms TTFT)
      → Complex scaffolding path: GPT-4o-mini (~180ms TTFT)
  → [Token Accumulator: sentence-boundary chunking]
  → [Streaming TTS: ElevenLabs v2 or Cartesia Sonic]
  → [Avatar Renderer: Simli with audio streaming]
  → Student screen

Parallel systems:
  → [Latency Instrumenter] → per-stage metrics → real-time overlay
  → [Socratic State Machine] → tracks learning arc → adapts prompt
  → [Turn Quality Evaluator] → post-turn Socratic quality scoring
```

### Key Design Decisions That Separate Top 1%

**1. Model Routing (not model selection)**

Average: Pick one LLM, use it for everything.
Top 1%: Route queries to different models based on complexity.

- **Acknowledgments / encouragement** ("That's it! How did you get there?"): Groq Llama-3.3-70B — ~80ms TTFT, sufficient quality for short responses
- **Scaffolding questions** (building on student's answer, redirecting wrong answers): GPT-4o-mini streaming — ~180ms TTFT, better pedagogical reasoning
- **Classification**: A tiny classifier (rule-based or small model) decides in <20ms

This demonstrates the candidate understands *latency-quality tradeoffs at the model level*, which is exactly what the Technical Innovation rubric rewards.

**2. Sentence-Boundary Token Accumulation**

Average: Stream every token to TTS immediately (causes choppy speech).
Top 1%: Accumulate tokens until a sentence boundary, then stream the complete sentence to TTS.

Why: TTS quality degrades with very short inputs. A complete sentence produces better prosody and more natural speech. The tradeoff is ~50-100ms additional latency for the first sentence vs. significantly better speech quality. Document this tradeoff explicitly.

**3. Socratic State Machine**

Average: One system prompt, same behavior throughout.
Top 1%: A state machine that tracks the tutoring conversation and adapts the LLM's behavior.

States:
```
OPENING → PROBE → SCAFFOLD → REDIRECT → CONFIRM → DEEPEN → CLOSE
```

- **OPENING**: Greet student, ask what they want to learn
- **PROBE**: Ask initial diagnostic question to gauge understanding
- **SCAFFOLD**: Build a sequence of guiding questions toward the concept
- **REDIRECT**: When student is wrong, ask a revealing question (don't correct)
- **CONFIRM**: When student is right, ask them to explain WHY
- **DEEPEN**: Add complexity or connect to related concepts
- **CLOSE**: Summarize what they discovered (through questions, not lecture)

The system prompt changes based on the current state. This produces dramatically better Socratic tutoring than a static prompt.

**4. Avatar Engagement Behavior**

Average: Avatar is static when not speaking.
Top 1%: Avatar has three behavioral modes:

- **Listening**: Subtle nodding, maintained eye contact, occasional "micro-expressions"
- **Thinking**: Brief pause with natural "processing" behavior (slight head tilt, eye movement) before responding — this actually MASKS latency by making 200-500ms feel intentional
- **Speaking**: Lip-synced speech with natural gestures

The "thinking" animation is a critical latency-hiding technique. It converts dead time into perceived engagement.

**5. Speculative Response Preparation**

Average: Wait for student to finish speaking, then start the pipeline.
Top 1%: While the student is speaking, pre-compute likely response patterns.

- After the student starts speaking, the Socratic State Machine can predict likely response categories (correct answer, incorrect answer, confusion, follow-up question)
- Pre-warm the LLM with context for each likely branch
- When the student finishes, the system already has a head start

This is hard to implement well but demonstrates genuine innovation. Even a partial implementation (pre-warming the LLM context) shows deep thinking.

---

## STEP 3 — Elite System Architecture

### Full Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│  ┌─────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Student  │  │ Avatar Video │  │ Latency Dashboard       │ │
│  │ Mic/Cam  │  │ (Simli SDK)  │  │ (per-stage, real-time)  │ │
│  └────┬─────┘  └──────▲───────┘  └────────▲────────────────┘ │
│       │               │                    │                  │
└───────┼───────────────┼────────────────────┼──────────────────┘
        │ WebSocket     │ WebRTC             │ WebSocket
        ▼               │                    │
┌───────────────────────┴────────────────────┴──────────────────┐
│                    ORCHESTRATOR (Python/Node)                  │
│                                                                │
│  ┌──────────┐    ┌──────────────┐    ┌─────────────────────┐  │
│  │   VAD    │───▶│ Streaming    │───▶│  Query Classifier   │  │
│  │ (Silero) │    │ STT          │    │  (rule-based,<20ms) │  │
│  │  ~30ms   │    │ (Deepgram)   │    │                     │  │
│  └──────────┘    │  ~150ms      │    └──────────┬──────────┘  │
│                  └──────────────┘               │              │
│                                                  ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    LLM ROUTER                             │  │
│  │  ┌─────────────────┐    ┌──────────────────────────────┐ │  │
│  │  │ Fast Path        │    │ Quality Path                 │ │  │
│  │  │ Groq Llama-3.3   │    │ GPT-4o-mini (streaming)     │ │  │
│  │  │ ~80ms TTFT       │    │ ~180ms TTFT                  │ │  │
│  │  │ (acks, short Qs) │    │ (scaffolding, redirects)     │ │  │
│  │  └────────┬─────────┘    └──────────────┬───────────────┘ │  │
│  └───────────┼─────────────────────────────┼─────────────────┘  │
│              └──────────────┬──────────────┘                    │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SENTENCE BOUNDARY CHUNKER                    │  │
│  │  Accumulates tokens → emits complete sentences           │  │
│  │  ~50ms additional latency for better TTS prosody         │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              STREAMING TTS                                │  │
│  │  ElevenLabs v2 / Cartesia Sonic                          │  │
│  │  ~120ms to first audio chunk                             │  │
│  │  Streams PCM16 audio chunks                              │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SIMLI AVATAR RENDERER                        │  │
│  │  Receives audio chunks → renders lip-synced video        │  │
│  │  ~80ms render latency                                    │  │
│  │  Idle/listening/thinking animations between turns        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ═══════════ PARALLEL SYSTEMS ═══════════                      │
│                                                                │
│  ┌───────────────────┐  ┌──────────────────────────────────┐  │
│  │ LATENCY           │  │ SOCRATIC STATE MACHINE            │  │
│  │ INSTRUMENTER      │  │                                    │  │
│  │                   │  │ States: OPENING → PROBE →          │  │
│  │ Timestamps every  │  │   SCAFFOLD → REDIRECT →            │  │
│  │ stage boundary    │  │   CONFIRM → DEEPEN → CLOSE         │  │
│  │                   │  │                                    │  │
│  │ Emits per-turn:   │  │ Adapts system prompt per state    │  │
│  │ - stt_ms          │  │ Tracks concepts taught            │  │
│  │ - llm_ttft_ms     │  │ Selects next question strategy    │  │
│  │ - tts_first_ms    │  │                                    │  │
│  │ - avatar_ms       │  │                                    │  │
│  │ - e2e_ms          │  │                                    │  │
│  │ - lip_sync_offset │  │                                    │  │
│  └───────────────────┘  └──────────────────────────────────┘  │
│                                                                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ BENCHMARKING & ANALYTICS                                   │ │
│  │                                                             │ │
│  │ - Per-turn latency log (JSON)                              │ │
│  │ - Aggregate statistics (mean, p50, p95, p99, variance)    │ │
│  │ - Per-stage latency distribution charts                    │ │
│  │ - Lip-sync offset measurement                              │ │
│  │ - Socratic quality scoring (post-session)                  │ │
│  │ - Cost tracking (tokens used, API costs per turn)         │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### How Each Component Demonstrates AI Engineering Ability

| Component | What It Demonstrates |
|---|---|
| **VAD + Streaming STT** | Real-time audio processing, understanding of voice activity detection tradeoffs |
| **Query Classifier + LLM Router** | Model routing, latency-quality tradeoffs, cost optimization |
| **Sentence Boundary Chunker** | Understanding of TTS quality vs latency tradeoffs, NLP-level token processing |
| **Streaming TTS** | Audio streaming, chunk-based processing, first-byte optimization |
| **Avatar with behavioral modes** | Latency-hiding techniques, UX engineering, perception management |
| **Latency Instrumenter** | Systems observability, performance engineering, benchmarking methodology |
| **Socratic State Machine** | Conversation design, prompt management, educational quality engineering |
| **Benchmarking & Analytics** | Data-driven optimization, experimental methodology, quantitative rigor |

---

## STEP 4 — Technical Features That Impress Reviewers

### 1. Per-Stage Latency Dashboard (visible in demo)

**What it is**: A real-time overlay during the tutoring session showing per-stage latency for every conversational turn.

```
┌──────────────────────────────────┐
│ Turn 7          E2E: 487ms       │
│ ├─ STT:          142ms  ████     │
│ ├─ LLM (TTFT):   118ms  ███     │
│ ├─ TTS (first):  139ms  ████    │
│ ├─ Avatar:        88ms  ██      │
│ └─ Overhead:       0ms           │
│                                  │
│ Session avg:     512ms           │
│ p95:             623ms           │
│ Lip-sync:        ±38ms          │
└──────────────────────────────────┘
```

**Why it impresses**: It proves the candidate understands the pipeline at a component level, not just "it works." It shows engineering discipline. A reviewer sees this and thinks "this person instruments their systems."

### 2. Model Routing with Documented Rationale

**What it is**: Different LLMs for different query types, with documented latency/quality comparison.

```
Decision: Route short responses to Groq, complex scaffolding to GPT-4o-mini

Evidence:
| Query Type        | Groq Llama-3.3 | GPT-4o-mini | Decision    |
|-------------------|----------------|-------------|-------------|
| Acknowledgment    | 78ms / 8.2/10  | 195ms / 8.5 | Groq (Δ117ms for Δ0.3 quality) |
| Scaffolding Q     | 82ms / 6.8/10  | 188ms / 8.7 | GPT-4o-mini (Δ106ms for Δ1.9 quality) |
| Redirect (wrong)  | 85ms / 6.2/10  | 192ms / 8.9 | GPT-4o-mini (Δ107ms for Δ2.7 quality) |
```

**Why it impresses**: This is exactly how production AI systems work. It demonstrates cost-latency-quality tradeoff analysis, which is what senior AI engineers do daily.

### 3. Latency Regression Tests

**What it is**: Automated tests that verify each pipeline stage stays within its latency budget.

```python
def test_stt_latency_budget():
    """STT must complete within 300ms (max acceptable) across 10 samples."""
    latencies = [measure_stt(sample) for sample in TEST_AUDIO_SAMPLES]
    p95 = np.percentile(latencies, 95)
    assert p95 < 300, f"STT p95 latency {p95}ms exceeds 300ms budget"

def test_e2e_latency_budget():
    """End-to-end must be <1000ms (required) across 10 full pipeline runs."""
    latencies = [measure_full_pipeline(sample) for sample in TEST_QUERIES]
    p95 = np.percentile(latencies, 95)
    assert p95 < 1000, f"E2E p95 latency {p95}ms exceeds 1000ms budget"

def test_lip_sync_alignment():
    """Lip-sync offset must be within ±80ms for 95% of frames."""
    offsets = measure_lip_sync(TEST_AUDIO, TEST_VIDEO)
    within_80 = sum(1 for o in offsets if abs(o) <= 80) / len(offsets)
    assert within_80 >= 0.95, f"Only {within_80:.0%} of frames within ±80ms"
```

**Why it impresses**: This shows the candidate treats latency as a first-class engineering constraint, not an afterthought. Latency regression tests are what real production systems have.

### 4. Socratic Quality Evaluation Framework

**What it is**: An automated post-session evaluation that scores each tutor turn on Socratic principles.

```python
SOCRATIC_RUBRIC = {
    "asks_guiding_question": "Does the response end with a question that guides understanding?",
    "avoids_direct_answer": "Does it avoid giving away the answer?",
    "builds_on_student": "Does it acknowledge and build on what the student said?",
    "grade_appropriate": "Is the language appropriate for the target grade level?",
    "advances_understanding": "Does the question move the student closer to the concept?"
}
```

Run an LLM evaluator (separate from the tutoring LLM) against the conversation transcript post-session. Report Socratic quality scores alongside latency metrics.

**Why it impresses**: This demonstrates the candidate can build evaluation frameworks — the hardest part of modern AI engineering. It shows they care about output quality, not just making it work.

### 5. Pipeline Configuration Comparison

**What it is**: Documented experiments comparing different pipeline configurations.

```
Configuration A: OpenAI Realtime + Simli
  E2E: 650ms avg | Lip-sync: ±52ms | Quality: 8.1/10
  Pros: Simple, reliable, good quality
  Cons: Black box, no per-stage control, higher cost

Configuration B: Deepgram + Groq + ElevenLabs + Simli
  E2E: 490ms avg | Lip-sync: ±41ms | Quality: 7.8/10
  Pros: Full per-stage visibility, swappable, cheaper
  Cons: More complex, more failure points

Configuration C: Deepgram + Groq + Cartesia + Simli
  E2E: 420ms avg | Lip-sync: ±38ms | Quality: 7.5/10
  Pros: Fastest, lowest cost
  Cons: Slightly lower voice quality

Decision: Configuration B as primary, with model routing optimization.
Rationale: Best balance of speed, quality, and observability.
```

**Why it impresses**: This is *experimentation*. The candidate didn't just pick one approach — they tried multiple, measured results, and made a data-driven decision. This is how top engineers work.

### 6. Cost-Per-Tutoring-Minute Analysis

**What it is**: Track API costs per conversational turn and compute cost per minute of tutoring.

```
Average turn:
  STT: $0.0003 (Deepgram, ~3s audio)
  LLM: $0.0008 (Groq, ~150 tokens)
  TTS: $0.0015 (ElevenLabs, ~80 chars)
  Avatar: $0.002 (Simli, ~5s video)
  Total per turn: ~$0.004

Turns per minute: ~4-6
Cost per tutoring minute: ~$0.02
Cost per 30-min session: ~$0.60

At scale (1000 concurrent sessions):
  Infrastructure: ~$X/hour
  API costs: ~$600/hour
  Total: ~$Y per session
```

**Why it impresses**: This is the +2 bonus for "production-ready cost analysis and scaling plan." It shows the candidate thinks about systems at scale, not just getting a demo working.

### 7. Thinking Animation as Latency Hiding

**What it is**: When the student finishes speaking, the avatar enters a natural "thinking" pose (slight head tilt, eye movement, thoughtful expression) for 200-400ms before the response audio begins.

**Why it impresses**: This converts dead pipeline latency into perceived attentiveness. A 500ms response with a 200ms "thinking" animation feels like 300ms of actual delay. This is a UX insight that demonstrates the candidate understands human perception, not just systems engineering.

---

## STEP 5 — The Demo That Wins

### Demo Structure (3-4 minutes)

**[0:00-0:15] Cold Open — The Wow Moment**

Open directly with the avatar greeting a student. No intro slides, no setup. The viewer immediately sees a natural-looking AI avatar saying: "Hey! What would you like to work on today?"

The student responds verbally. The avatar responds in <1 second with a guiding question.

*What the viewer feels*: "This is real. This is fast. This feels like a conversation."

**[0:15-1:30] Socratic Sequence — The Substance**

The avatar teaches a specific concept (e.g., 8th grade: "Why does anything divided by zero not have an answer?") through a sequence of 4-5 guiding questions:

1. Avatar: "If you have 12 cookies and share them among 3 friends, how many does each friend get?"
2. Student: "4"
3. Avatar: "Right! Now what if you tried to share them among zero friends? What would that even mean?"
4. Student: "Uh... you can't do that?"
5. Avatar: "Why not? What happens if you try?"
6. Student: "There's nobody to give them to... so you can't divide?"
7. Avatar: "Exactly! You just discovered something mathematicians figured out too. Can you put that into a rule?"

The viewer watches the student *discover* the concept through questioning. Each turn takes <1 second.

*What the viewer feels*: "This is genuinely good teaching. And it's happening in real-time."

**[1:30-2:15] Wrong Answer Handling — The Intelligence**

The student gives a wrong answer. The avatar doesn't say "wrong" — it asks a question that reveals the error:

Student: "So zero divided by zero is also impossible?"
Avatar: "Interesting thought. Let me ask you this — if you have zero cookies and share them among 5 friends, how many does each friend get?"
Student: "Zero?"
Avatar: "Right! So zero divided by something IS possible. What's different about dividing BY zero?"

*What the viewer feels*: "The AI adapted. It didn't just follow a script."

**[2:15-2:45] The Technical Proof — The Engineering**

Brief overlay showing the latency dashboard:
- Per-turn latency breakdown for the last 5 turns
- Session averages: E2E 480ms, lip-sync ±39ms
- Model routing decisions highlighted

*What the viewer feels*: "This person measured everything. They know exactly where every millisecond goes."

**[2:45-3:15] Pipeline Comparison — The Depth**

30-second side-by-side comparison: same question processed through two different pipeline configurations, showing the latency difference and quality tradeoff.

*What the viewer feels*: "They didn't just build one pipeline — they experimented and optimized."

**[3:15-3:30] Close**

Avatar wraps up the lesson: "You figured that out yourself! Division by zero is undefined because there's no number that works. Great thinking today."

### What Differentiates This Demo

1. **Starts with the product, not the tech.** The viewer experiences the tutoring before seeing any metrics. This is how product-minded engineers present work.

2. **The Socratic method is visibly excellent.** The tutor never lectures, adapts to wrong answers, and produces a genuine learning arc. This is 25% of the score.

3. **The latency is felt, not just claimed.** The conversation flows naturally. The viewer doesn't need to read metrics to know it's fast.

4. **The technical overlay proves rigor.** Per-stage latency visible in real-time. The candidate isn't just claiming sub-second — they're showing the breakdown.

5. **The comparison shows experimentation.** Side-by-side pipeline comparison proves the candidate explored the design space.

---

## STEP 6 — Risks That Could Ruin the Submission

### Risk 1: Overengineering the Avatar

**The trap**: Spending 5 days trying to build a custom avatar renderer with SadTalker/Wav2Lip instead of using Simli.

**Why it's dangerous**: Open-source avatar generation is slow (often >500ms per frame) and produces uncanny results. You'll blow your latency budget AND produce a worse-looking avatar than a managed API.

**How to avoid**: Use Simli for the avatar. Invest your time in the pipeline, instrumentation, and educational quality — these are where the scoring weight is.

### Risk 2: Ignoring Educational Quality (25% of score)

**The trap**: Spending all time on latency optimization and treating the Socratic method as a prompt engineering afterthought.

**Why it's dangerous**: Educational Quality has EQUAL weight to Latency Performance (25% each). A fast system that lectures instead of questioning gets an automatic -10 deduction AND scores poorly on 25% of the rubric. You'd lose 20-35 points.

**How to avoid**: Build the Socratic State Machine early. Test it with multiple conversation paths. Have someone actually try the tutor and evaluate whether it asks good questions.

### Risk 3: Sequential Pipeline

**The trap**: Building the pipeline stages sequentially (STT finishes → LLM starts → LLM finishes → TTS starts → etc.)

**Why it's dangerous**: Sequential execution adds latency multiplicatively. STT(300ms) + LLM(400ms) + TTS(300ms) + Avatar(200ms) = 1200ms minimum. This CANNOT hit <1s. The rubric automatically deducts 10 points for >3s.

**How to avoid**: Stream everything. LLM tokens stream to TTS as they're generated. TTS audio chunks stream to the avatar as they're synthesized. This is the core architectural insight.

### Risk 4: No Per-Stage Latency Breakdown

**The trap**: Only measuring end-to-end latency.

**Why it's dangerous**: Automatic -10 point deduction. The submission checklist requires "Per-stage latency breakdown reported (STT, LLM, TTS, avatar rendering)."

**How to avoid**: Instrument from day 1. Every stage boundary gets a `time.perf_counter()` timestamp. Export per-turn metrics as JSON.

### Risk 5: Weak Demo Video

**The trap**: Screen recording of a stilted interaction where the student reads scripted questions and the avatar responds slowly.

**Why it's dangerous**: The demo video is the PRIMARY artifact for evaluating Educational Quality (25%) and Video Integration (15%). A bad demo loses 40% of available points. No demo = automatic -15.

**How to avoid**: Practice the demo interaction multiple times. Use a real conversation, not a script. Make sure the concepts are clear (pick topics you understand well). Record multiple takes and use the best one.

### Risk 6: Trying to Build Everything, Shipping Nothing

**The trap**: Attempting model routing + speculative generation + custom avatar + full dashboard + cost analysis and running out of time with nothing working.

**Why it's dangerous**: A working basic pipeline beats an ambitious non-working system every time. The rubric has heavy automatic deductions for non-functional components.

**How to avoid**: Strict priority ordering. Get the basic streaming pipeline working FIRST (Phase 1). Everything else is optimization on top of a working foundation.

---

## STEP 7 — Concrete Implementation Roadmap

### Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| **Frontend** | Next.js 14 + React | Server components for orchestration, React for real-time UI |
| **Orchestrator** | Python (FastAPI + asyncio) OR Node.js | Manages pipeline, WebSocket connections |
| **VAD** | Silero VAD | Fast, accurate, runs locally |
| **STT** | Deepgram Nova-2 (streaming) | ~150ms, streaming WebSocket API, excellent accuracy |
| **LLM (fast)** | Groq (Llama-3.3-70B) | ~80ms TTFT, free/cheap, streaming |
| **LLM (quality)** | OpenAI GPT-4o-mini (streaming) | ~180ms TTFT, better pedagogical reasoning |
| **TTS** | ElevenLabs v2 (streaming) OR Cartesia Sonic | ~120ms first byte, streaming, natural voice |
| **Avatar** | Simli | Real-time lip-sync from audio stream, <100ms render |
| **Transport** | WebSocket (client↔server), WebRTC (avatar video) | Low-latency bidirectional communication |
| **Metrics** | Custom instrumentation → JSON logs | Per-stage timestamps, aggregation |
| **Tests** | pytest (Python) or vitest (Node) | Latency regression, integration, unit |

### Development Phases

#### Phase 1: Working Pipeline (Days 1-3)
**Goal**: Student speaks → avatar responds with voice and video, end-to-end.

- [ ] Set up project structure (orchestrator, frontend)
- [ ] Implement audio capture from browser mic → WebSocket to server
- [ ] Integrate Silero VAD for endpoint detection
- [ ] Connect Deepgram streaming STT
- [ ] Connect Groq LLM with streaming (basic Socratic system prompt)
- [ ] Connect ElevenLabs/Cartesia streaming TTS
- [ ] Connect Simli avatar with audio streaming
- [ ] Get end-to-end working (even if slow/buggy)
- [ ] Add basic per-stage timestamp logging

**Milestone**: You can speak to the avatar and get a voiced, lip-synced response. Latency doesn't matter yet.

#### Phase 2: Streaming Pipeline + Instrumentation (Days 3-5)
**Goal**: All stages stream into each other. Latency <1s. Full instrumentation.

- [ ] Implement true streaming: LLM tokens → sentence chunker → TTS → avatar
- [ ] Add per-stage latency instrumentation (timestamps at every boundary)
- [ ] Build latency metrics aggregation (mean, p50, p95, variance)
- [ ] Create JSON log format for per-turn metrics
- [ ] Implement avatar idle/listening/thinking behavioral modes
- [ ] Optimize: identify bottleneck, reduce largest contributor
- [ ] Target: <1s E2E consistently

**Milestone**: Streaming pipeline working. Latency instrumented and consistently <1s.

#### Phase 3: Socratic Quality (Days 5-7)
**Goal**: Excellent Socratic tutoring for 2 concepts. State machine working.

- [ ] Design Socratic State Machine (OPENING → PROBE → SCAFFOLD → REDIRECT → CONFIRM → DEEPEN → CLOSE)
- [ ] Create state-specific system prompts
- [ ] Choose 2 concepts: one 6th-8th grade (e.g., fractions or division by zero), one 9th-10th grade (e.g., photosynthesis or cell division)
- [ ] Design question sequences for each concept
- [ ] Test with real conversations — iterate on prompts until tutor never lectures
- [ ] Implement model routing (fast path for acks, quality path for scaffolding)
- [ ] Build query classifier (rule-based is fine)

**Milestone**: The tutor can guide a student through 2 concepts using only questions. Natural conversation flow.

#### Phase 4: Benchmarking & Documentation (Days 7-9)
**Goal**: Comprehensive benchmarking framework. Tests. Documentation.

- [ ] Build latency benchmarking script (runs N conversations, reports statistics)
- [ ] Write latency regression tests (per-stage and E2E)
- [ ] Measure lip-sync alignment (methodology + results)
- [ ] Build Socratic quality evaluator (LLM-as-judge on conversation transcripts)
- [ ] Document pipeline configuration experiments (if time: compare 2-3 configs)
- [ ] Compute cost-per-tutoring-minute analysis
- [ ] Write decision log (what you tried, what worked, what didn't, WHY)
- [ ] Document limitations honestly

**Milestone**: Full benchmarking framework with per-stage results. 15+ tests. Decision log complete.

#### Phase 5: Demo & Polish (Days 9-10)
**Goal**: Record an excellent 3-4 minute demo video.

- [ ] Build real-time latency overlay for demo (optional but impressive)
- [ ] Practice 3-5 tutoring conversations
- [ ] Record multiple takes of the demo
- [ ] Include: cold open, Socratic sequence, wrong answer handling, latency metrics
- [ ] Optional: brief side-by-side pipeline comparison
- [ ] Write README with one-command setup
- [ ] Final cleanup, ensure reproducibility

**Milestone**: Demo video recorded. Submission complete.

### Priority Rules

1. **A working streaming pipeline > a perfect static pipeline.** Get streaming working before optimizing.
2. **Socratic quality > sub-500ms latency.** Both are 25% of the score, but lecturing has an automatic -10 deduction.
3. **Per-stage instrumentation > novel optimizations.** Missing latency breakdown is -10. Novel optimization is +3 bonus.
4. **A good demo > good documentation.** Demo is the primary artifact. Documentation supports it.
5. **Depth over breadth.** Do fewer features well rather than many features poorly.

---

## STEP 8 — Final Advice

### Be Blunt

**1. The demo video is the single most important artifact.** Reviewers will watch your demo before reading a single line of code. If the demo shows a natural AI conversation at sub-second latency with a video avatar using the Socratic method — you've already won. If the demo shows a stilted, slow, lecturing chatbot with a glitchy face — nothing else saves you.

**2. Instrument everything from day 1.** Don't add latency measurement at the end. The per-stage breakdown is REQUIRED (automatic -10 if missing) and is the backbone of your Technical Innovation score. Every pipeline stage should have `start_time` and `end_time` from the first working version.

**3. The Socratic method is not optional — it's 25% of your grade.** Many candidates will treat it as a prompt afterthought. Build the state machine. Test with real conversations. Make sure the tutor NEVER gives a direct answer. This is the easiest way to score above the median because most submissions will lecture.

**4. Use managed APIs for the avatar. Don't be a hero.** Simli gives you a good-looking, lip-synced avatar with <100ms render latency. Building your own with SadTalker/Wav2Lip will take days and produce worse results. Spend that time on pipeline optimization and Socratic quality.

**5. The composable pipeline (Approach B) is worth the complexity.** Yes, it's harder than the collapsed pipeline (Approach A). But it gives you per-stage visibility, model routing capability, and the ability to demonstrate that you understand each component. The Technical Innovation rubric (15%) explicitly rewards "per-component latency budget analysis" and "creative architecture decisions." You can't demonstrate these with a black box.

**6. Document your failures, not just your successes.** The evaluation criteria value honest documentation of limitations. Write in your decision log: "I tried X, it didn't work because Y, so I switched to Z." This is more impressive than pretending everything worked perfectly.

**7. Don't optimize prematurely.** Phase 1 is a working pipeline, even if it's 2 seconds E2E. Phase 2 is streaming optimization. Phase 3 is Socratic quality. If you skip to optimization before having a working system, you'll have an optimized nothing.

**8. The thinking animation is free latency.** When the avatar enters a "thinking" pose for 200ms before responding, you've just hidden 200ms of pipeline latency. This is the cheapest, highest-impact optimization you can make. Implement it.

**9. Pick concepts you genuinely understand.** If you're teaching 8th grade fractions, you need to know fractions well enough to design a Socratic question sequence that guides a student from confusion to understanding. Don't pick calculus if you can't write 6 scaffolding questions off the top of your head.

**10. Ship the simplest version that meets all requirements first, then improve.** The submission checklist has 11 items. Make sure you hit every single one before adding any bells and whistles. A complete submission that meets all requirements beats an impressive incomplete submission every time.
