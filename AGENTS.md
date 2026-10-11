# JARVIS Agents

This document describes the autonomous agents that power JARVIS.

## Overview

JARVIS is built on a multi-agent architecture where specialized agents handle different domains:

```
┌─────────────────────────────────────────────┐
│     Main Conversation Agent (LLM)           │
│  • Understands user intent                  │
│  • Plans multi-step tasks                   │
│  • Asks clarifying questions                │
│  • Coordinates other agents                 │
└─────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │   Tool     │ │  Browser   │ │   Vision   │
    │  Planner   │ │   Agent    │ │   Agent    │
    └────────────┘ └────────────┘ └────────────┘
         │              │              │
         ▼              ▼              ▼
    [Tool Execution] [Navigation] [Analysis]
```

## Agents (Planned)

### 1. Main Conversation Agent
**Status:** Phase 1  
**Role:** Central coordinator  
**Responsibilities:**
- Understand natural language input
- Maintain conversation context
- Plan task execution
- Ask clarifying questions
- Route to specialized agents
- Remember past interactions

**Key Features:**
- Context-aware responses
- Multi-turn conversations
- Error recovery
- Personality & tone

---

### 2. Tool Planner & Validator
**Status:** Phase 1  
**Role:** Controlled tool execution  
**Responsibilities:**
- Receive tool requests from LLM
- Validate against allowlist
- Check safety constraints
- Execute approved tools
- Return results to LLM

**Execution Pipeline:**
```
LLM → Tool Request
  ↓
Tool Planner
  ↓
Validate (Allowlist, Security)
  ↓
Execute Tool
  ↓
Return Result
  ↓
LLM
```

**Security:**
- ✅ Whitelist-only execution (no arbitrary commands)
- ✅ Input validation
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Permission checks

---

### 3. Browser Agent
**Status:** Phase 2  
**Role:** Web automation & research  
**Responsibilities:**
- Open Firefox with Geckodriver
- Navigate to URLs
- Fill forms
- Click buttons
- Extract information
- Research information online

**Constraints:**
- Must use official APIs when available
- Respect robots.txt & ToS
- Fail gracefully on network errors

---

### 4. Vision Agent
**Status:** Phase 2  
**Role:** Screen analysis  
**Responsibilities:**
- Capture screenshots
- Analyze UI elements
- Identify clickable regions
- Read text on screen
- Provide context to LLM

**Models:**
- Vision model (Claude, GPT-4V, or local alternative)
- OCR for text extraction

---

### 5. PC Control Agent
**Status:** Phase 3  
**Role:** Windows automation  
**Responsibilities:**
- Open/close programs
- Manage files & folders
- Read system info
- Execute defined Windows actions
- Monitor processes

**Tools:**
- `open_program(name)` - Launch application
- `close_program(name)` - Terminate process
- `file_operation(op, path)` - Copy, move, delete files
- `system_info()` - CPU, RAM, disk, network
- `screenshot()` - Capture screen

---

### 6. OBS Agent
**Status:** Phase 3  
**Role:** Streaming control  
**Responsibilities:**
- Detect OBS setup
- List profiles & scenes
- Start/stop streaming
- Change scenes
- Read OBS status

**Integration:**
- OBS WebSocket API
- Defined control functions (no arbitrary scripts)

---

### 7. Memory Agent
**Status:** Phase 1 (Basic)  
**Role:** Store & retrieve information  
**Responsibilities:**
- Store facts about user
- Recall past conversations
- Track preferences
- Manage task history

**Storage:**
- Local database (SQLite initially, upgradeable)
- Structured queries
- Vector embeddings (for semantic search)

---

### 8. Sync Agent
**Status:** Phase 1  
**Role:** Windows ↔ Android synchronization  
**Responsibilities:**
- Detect sync events
- Upload changes from Android
- Download changes to Android
- Conflict resolution
- Offline handling

**Sync Model:**
```
Android                        PC
   │                           │
   ├─ Create Task              │
   │  (offline)                │
   │                           │
   ├─ (PC comes online)        │
   │  Detect change            │
   ├──────────────────────────→
   │  Sync to PC               │
   │                    Process & merge
   │← ──────────────────────── 
   │  Confirm                  │
```

---

## Communication & Safeguards

### Tool Execution Safeguards

**Before Execution:**
1. Tool is on allowlist ✓
2. Input is validated ✓
3. No destructive action without confirmation ✓
4. Rate limits OK ✓

**After Execution:**
1. Result is captured ✓
2. Error handling ✓
3. Audit log entry ✓
4. Return to LLM ✓

### Dangerous Operations

Actions that require explicit confirmation:
- Delete files (>1MB or system files)
- Terminate critical processes
- Modify system settings
- Execute scripts

Requested format:
```
JARVIS: "This will delete C:\Documents\old_files. Are you sure?"
User: "Yes, proceed." ✓
```

---

## LLM Models

### Planned Model Tiers

| Component | Model | Notes |
|-----------|-------|-------|
| Main Conversation | GPT-4 / Claude | Latest large model |
| Tool Planning | GPT-4 / Claude | Reliable for structured output |
| Coding | Claude/Copilot | For development tasks |
| Vision | GPT-4V / Claude Vision | Screen & image analysis |
| Memory Query | Embedding model | Semantic search |

### Fallback Strategy
- Primary → Secondary → Tertiary
- Graceful degradation when service unavailable
- Cache responses when possible

---

## Future Enhancements

- [ ] Multi-language support
- [ ] Custom training on user behavior
- [ ] Proactive suggestions based on patterns
- [ ] Real-time collaboration with other users
- [ ] Advanced tool composition
- [ ] Learning from feedback

---

## Development Status

| Agent | Status | Phase | Owner |
|-------|--------|-------|-------|
| Main Conversation | 🟡 In Progress | 1 | TBD |
| Tool Planner | 🟡 In Progress | 1 | TBD |
| Memory | 🟡 In Progress | 1 | TBD |
| Sync | 🟡 In Progress | 1 | TBD |
| Browser | 🟢 Planned | 2 | TBD |
| Vision | 🟢 Planned | 2 | TBD |
| PC Control | 🟢 Planned | 3 | TBD |
| OBS | 🟢 Planned | 3 | TBD |
