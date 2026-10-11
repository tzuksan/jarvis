# JARVIS Architectural Decision Records (ADR)

This document tracks important architectural decisions made during JARVIS development.

---

## ADR-001: Modular Multi-Agent Architecture

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

JARVIS needs to handle diverse tasks: conversations, tool execution, browser automation, vision, streaming control, etc. A monolithic approach would become unmaintainable quickly.

**Decision:**

Use a **multi-agent architecture** where:
- Each agent has a specific domain (conversation, browser, PC control, etc.)
- Agents communicate via well-defined protocols (WebSocket, REST)
- The main conversation agent acts as a coordinator
- Tool execution goes through a validation pipeline

**Alternatives Considered:**
1. **Monolithic Python app** - Simple initially, becomes unwieldy; hard to parallelize
2. **Microservices on Docker** - Overkill for Phase 1; adds complexity
3. **Plugin-based system** - Good for extensibility, but harder for core cohesion

**Rationale:**
- Enables independent development of components
- Allows scaling (Phase 4: separate PC control from conversation)
- Clear separation of concerns
- Easier testing and debugging

**Consequences:**
- ✅ Code is modular and testable
- ✅ Easy to add new agents (Phase 2+)
- ⚠️ More complex communication layer
- ⚠️ Debugging distributed issues harder

**Follow-up:** Will use message queues (later phases) if needed.

---

## ADR-002: Tool Allowlist & Validation Pipeline

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

LLMs can hallucinate or be misused. Allowing arbitrary LLM outputs to run as shell commands is a security disaster.

**Decision:**

Implement a **strict allowlist-based tool system:**

```
LLM Request → Tool Planner → Validation → Execution → Result
                           ↓
                      Allowlist check
                      Input validation
                      Permission checks
```

**Allowlist contains:**
- Tool name (e.g., "open_program")
- Allowed parameters
- Whitelist of safe inputs (e.g., approved programs)
- Rate limits

**Alternatives Considered:**
1. **No validation** - Dangerous, violates rule #14
2. **Regex-based filters** - Too permissive, easily bypassed
3. **Sandbox execution** - Complex, still risky with direct shell access
4. **Allowlist + sandboxing** - Planned for Phase 4+

**Rationale:**
- Prevents accidental & malicious misuse
- Clear audit trail (security logging)
- User can understand what JARVIS can do
- Scales well (add new tools incrementally)

**Consequences:**
- ✅ Very secure (layered defense)
- ✅ Transparent to users
- ⚠️ Can't do arbitrary actions
- ⚠️ Adding new tools requires code review

**Follow-up:** Will add confirmation dialogs for destructive actions (delete files, etc.).

---

## ADR-003: Bidirectional Android ↔ PC Sync

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

JARVIS must work when:
- PC is offline (Android queues)
- Android is offline (PC continues)
- Both are online (live sync)

**Decision:**

Implement **bidirectional sync with offline queues:**

**Architecture:**
```
Android (Client)          Network          PC (Server)
   ↓                                          ↓
Local DB + Queue          Sync                 Main DB
   ↓                      (WebSocket)          ↓
Detect offline --------→ Queue events ←----- Process
   ↓                                          ↓
Retry on reconnect ←-------- Sync back --→ Confirm
```

**Features:**
- Offline queue on both platforms
- Conflict detection (last-write-wins initially)
- Sync status visible to user
- Auto-retry with exponential backoff
- Bidirectional sync (changes flow both ways)

**Alternatives Considered:**
1. **PC-only persistence** - Doesn't work when PC offline
2. **Cloud-only sync** - Adds complexity & cost (Phase 4+)
3. **Pull-only (PC always asks)** - Inefficient, high latency
4. **Unidirectional (Android → PC only)** - Misses PC → Android updates

**Rationale:**
- Works offline on both platforms
- Consistent data across devices
- No complex server required (Phase 1)
- Scales to cloud later

**Consequences:**
- ✅ Fully functional when either device offline
- ✅ No central server dependency
- ⚠️ Conflict handling complexity
- ⚠️ Potential for data divergence if bugs exist

**Follow-up:**
- Phase 2: Add timestamp-based conflict resolution
- Phase 4: Add cloud-based "source of truth"

---

## ADR-004: SQLite for Phase 1, Upgrade Path for Phase 4+

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

Need persistent storage for conversations, tasks, memory. SQLite vs PostgreSQL vs other?

**Decision:**

**Phase 1-3: SQLite**
- Local database on PC & Android
- No server overhead
- Simple deployment
- Sufficient for single-user use

**Phase 4+: PostgreSQL** (optional)
- If multi-device/multi-user needed
- Cloud-hosted database
- Proper access control
- Backup capabilities

**Schema Design:**
- Use SQLAlchemy ORM (Python)
- Room (Kotlin, Android)
- Both support easy migration to PostgreSQL

**Alternatives Considered:**
1. **PostgreSQL from start** - Overkill, adds DevOps complexity
2. **MongoDB** - Wrong model (JARVIS needs relational data)
3. **DynamoDB/Firebase** - Cloud lock-in, cost issues
4. **In-memory only** - Data loss on restart, unacceptable

**Rationale:**
- SQLite = "it just works" (no server)
- Schema is simple enough to migrate later
- Good for development & testing
- Perfect for single-user/device setup

**Consequences:**
- ✅ Simple setup, no database server
- ✅ Easy backup (single file)
- ✅ Free & open source
- ⚠️ Not ideal for concurrent users (Phase 5)
- ⚠️ Will need migration script when scaling

**Upgrade Path (Phase 4):**
```
SQLite → Export as JSON → PostgreSQL Import
```

---

## ADR-005: FastAPI + WebSocket for PC Agent

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

PC Agent needs to serve API to Android app. What framework?

**Decision:**

Use **FastAPI + WebSocket:**
- FastAPI for REST endpoints (health, status, etc.)
- WebSocket for bidirectional real-time communication
- Runs via Uvicorn (ASGI server)

**Architecture:**
```
Android    ─── WebSocket ──→ PC Agent (FastAPI)
               ←─ JSON ←─

Fallback:  ─── REST (HTTP) ──→ (if WebSocket unavailable)
```

**Alternatives Considered:**
1. **Django** - Heavier, more batteries included, slower
2. **Flask** - Lighter, but poor async support
3. **gRPC** - Overkill, harder for mobile
4. **Plain asyncio** - Too low-level, reinvent wheels

**Rationale:**
- Modern Python web framework
- Excellent async support (uvicorn)
- WebSocket built-in
- Great documentation
- Type hints (Pydantic)
- Easy to test with Starlette test client

**Consequences:**
- ✅ Fast, modern, async
- ✅ Good Android compatibility
- ⚠️ Python-only (Phase 3: could expose REST API)

**Follow-up:** Phase 3 may add REST API for other clients.

---

## ADR-006: Local LLM Fallback in Phase 4+

**Status:** 🟡 Planned  
**Date:** 2026-09-25  
**Context:**

Relying solely on cloud APIs (OpenAI, Anthropic) creates:
- Dependency on external services
- Recurring costs
- Potential for throttling
- Privacy concerns

**Decision:**

**Phase 1-2: Cloud LLM (OpenAI/Claude)**
- Optimal performance & quality
- Lower development complexity
- Costs reasonable for single-user

**Phase 3: Prepare for local model**
- Evaluate open source models (Llama 2, Mistral, etc.)
- Test on GPU-enabled Windows PC
- Build abstraction layer

**Phase 4+: Local LLM Option**
- Deploy llama.cpp or similar
- Use with GPU acceleration
- Keep cloud as optional fallback

**Alternatives Considered:**
1. **Cloud-only forever** - Simpler, not independent
2. **Local-only** - Too slow in Phase 1-2, needs GPU
3. **Hybrid from start** - Complex, premature optimization

**Rationale:**
- Best of both worlds: fast cloud + independent local option
- Respects user privacy (data stays local eventually)
- Future-proof (doesn't depend on any single provider)
- Aligns with open-source philosophy

**Consequences:**
- ✅ Long-term independence
- ✅ Privacy-respecting
- ⚠️ More code paths to maintain
- ⚠️ Local model quality may differ

**Follow-up:** Will create abstraction in Phase 2.

---

## ADR-007: Voice I/O with Whisper + Edge TTS (Phase 1), Local Options (Phase 4+)

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

Speech-to-Text & Text-to-Speech are core to JARVIS's vision.

**Decision:**

**Phase 1: Cloud APIs**
- **STT:** OpenAI Whisper API (best accuracy, 25¢ per 60 min)
- **TTS:** Edge TTS (free, good quality)

**Phase 4+: Local alternatives**
- **STT:** Coqui STT or Whisper.cpp (local)
- **TTS:** Piper TTS or Coqui (local, offline)

**Fallback chain:**
```
Cloud Whisper → Whisper.cpp → Fallback text input
Cloud Edge TTS → Piper TTS → Fallback text output
```

**Alternatives Considered:**
1. **Google Speech** - Cost, API limitations
2. **Azure Speech** - Works, but expensive long-term
3. **Local-only** - Too slow/inaccurate for Phase 1
4. **Free APIs** - Less reliable, ToS issues

**Rationale:**
- Whisper is best STT accuracy
- Edge TTS is free & good quality
- Clear path to offline models

**Consequences:**
- ✅ Best quality in Phase 1-3
- ✅ Free TTS option available
- ⚠️ Depends on Whisper API costs
- ⚠️ Requires internet for Phase 1-3

**Follow-up:** Monitor local model quality, switch when ready.

---

## ADR-008: Kotlin + Jetpack Compose for Android UI

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

Android UI framework choice affects long-term maintainability and modern UX.

**Decision:**

Use **Kotlin + Jetpack Compose:**
- Modern declarative UI framework
- Kotlin is more expressive than Java
- Material Design 3 support
- Active Google development

**Architecture:**
- **UI:** Jetpack Compose (composables)
- **Data:** Room (local SQLite)
- **Async:** Coroutines + Flow
- **Navigation:** Jetpack Navigation Compose
- **DI:** Hilt

**Alternatives Considered:**
1. **Java + XML layouts** - Outdated, verbose
2. **Flutter** - Cross-platform, but locks us out of future iOS
3. **React Native** - JavaScript ecosystem, not ideal for this project
4. **Jetpack legacy** (XML + Activities) - Being phased out

**Rationale:**
- Compose is the future of Android (Google's direction)
- Kotlin is safer, more expressive
- MVVM pattern cleanly separates concerns
- Modern, well-supported tooling

**Consequences:**
- ✅ Modern, maintainable codebase
- ✅ Excellent tooling
- ⚠️ Compose API still evolving (rare breaking changes)
- ⚠️ Requires Android 5.0+ (acceptable)

**Follow-up:** Ensure comprehensive testing of Compose components.

---

## ADR-009: Agentic Orchestration vs. Imperative Workflows

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

JARVIS needs to execute complex, multi-step tasks. Should these be explicitly programmed or let the LLM plan?

**Decision:**

**Hybrid approach:**
- **Pre-defined workflows** for common tasks (e.g., "start streaming")
- **Agentic planning** for novel requests
- **User confirmation** for destructive actions

**Example:**
```
User: "I want to stream."
JARVIS: [Ask clarifying questions]
JARVIS: [Check predefined "setup streaming" workflow]
JARVIS: [Execute workflow with LLM-decided parameters]
User: [Confirms before destructive actions]
```

**Alternatives Considered:**
1. **Pure LLM planning** - Flexible but risky, unpredictable
2. **Fully scripted workflows** - Safe but inflexible, not truly "assistive"
3. **PDDL/planning formalism** - Overkill, steep learning curve

**Rationale:**
- Combines LLM's flexibility with reliability of predefined workflows
- Users understand what will happen (transparency)
- Safer than pure agentic execution
- Scales well (add workflows incrementally)

**Consequences:**
- ✅ Reliable multi-step execution
- ✅ User-controlled safety
- ⚠️ Need to maintain workflow library
- ⚠️ Not fully autonomous yet

**Follow-up:** Phase 4 will add more sophisticated workflow composition.

---

## ADR-010: Privacy-First Design (Local-First)

**Status:** ✅ Decided  
**Date:** 2026-09-25  
**Context:**

JARVIS handles personal data (tasks, preferences, conversations). Should this be cloud-based?

**Decision:**

**Privacy-first, local-first architecture:**
- All data stored locally by default (Windows PC + Android device)
- Cloud optional (Phase 4+, with user consent)
- No cloud dependency for core functionality
- Encryption for sync in transit

**Data Handling:**
- Conversations: Stored locally
- Tasks: Stored locally
- Memory: Stored locally
- Sync: Encrypted in transit, syncs between local devices

**Alternatives Considered:**
1. **Cloud from start** - Convenient, but privacy risk
2. **Hybrid with cloud** - Balances convenience & privacy
3. **Pure local, no cloud ever** - Limits multi-device later
4. **User choice** - Too complex for Phase 1

**Rationale:**
- Respects user privacy (their data is theirs)
- No vendor lock-in
- Works offline
- Aligns with JARVIS philosophy (personal assistant)

**Consequences:**
- ✅ Maximum privacy
- ✅ Offline-capable
- ⚠️ No automatic cloud backup (Phase 1)
- ⚠️ Multi-device sync simpler but requires LAN access

**Follow-up:** Phase 4 will add optional cloud backup with end-to-end encryption.

---

## Summary Table

| ADR | Title | Status | Decision |
|-----|-------|--------|----------|
| 001 | Multi-Agent Architecture | ✅ | Modular agents, central coordinator |
| 002 | Tool Validation | ✅ | Allowlist + validation pipeline |
| 003 | Sync Strategy | ✅ | Bidirectional with offline queues |
| 004 | Database | ✅ | SQLite (Phase 1-3), PostgreSQL upgrade path |
| 005 | PC Agent API | ✅ | FastAPI + WebSocket |
| 006 | LLM Fallback | 🟡 | Cloud (Phase 1-3), local option (Phase 4+) |
| 007 | Voice I/O | ✅ | Whisper + Edge TTS, local fallback later |
| 008 | Android UI | ✅ | Kotlin + Jetpack Compose + MVVM |
| 009 | Task Execution | ✅ | Hybrid: workflows + agentic planning |
| 010 | Privacy | ✅ | Local-first, cloud optional |

---

## How to Add New ADRs

When making significant architectural decisions:

1. Copy the template below
2. Fill in all sections
3. Get team review
4. Merge to `main` with decision final

### Template

```markdown
## ADR-XXX: [Title]

**Status:** 🟡 Proposed (or ✅ Decided or 🔄 Revisiting)
**Date:** YYYY-MM-DD
**Context:**

[What's the problem? Why does this decision matter?]

**Decision:**

[What did we decide?]

**Alternatives Considered:**
1. [Option A] - [Why rejected]
2. [Option B] - [Why rejected]

**Rationale:**

[Why this decision is best]

**Consequences:**
- ✅ [Benefit]
- ⚠️ [Trade-off]

**Follow-up:**

[Any future refinements planned?]
```

---

Last updated: 2026-09-25
