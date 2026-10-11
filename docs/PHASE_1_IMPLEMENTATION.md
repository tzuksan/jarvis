# JARVIS Phase 1 - Technical Implementation Plan

**Phase:** Foundation & Core Infrastructure  
**Duration:** 4-6 weeks  
**Goal:** Build a stable, modular foundation for JARVIS  

---

## Phase 1 Overview

Phase 1 focuses on:
1. **Conversation Engine** - Natural language understanding with context
2. **Memory System** - Persistent storage of facts and history
3. **Tool System** - Validated, allowlist-based tool execution
4. **Sync Foundation** - Android ↔ PC bidirectional sync
5. **Voice I/O Basics** - Whisper STT + Edge TTS integration
6. **Android UI - v0.1** - Minimal but functional mobile interface

**Success Criteria:**
- JARVIS responds to text input with conversational context
- Conversations are saved and retrievable
- Simple tools execute safely
- Android can queue tasks when PC is offline
- PC processes queued tasks when coming online
- Voice input/output works (basic)
- Both platforms have synchronized task lists

---

## Sprint Breakdown

### Sprint 1 (Weeks 1-2): Core AI Infrastructure
**Focus:** LLM integration, conversation management, local memory basics

#### Tasks

**1.1 - LLM Integration (3 days)**
- [ ] Set up FastAPI project structure
- [ ] Create OpenAI API wrapper
  - `ai_core/models/llm.py` - GPT-4 interface
  - Support: text generation, function calling
  - Implement response formatting (structured output)
- [ ] Error handling & retries
- [ ] Caching layer for repeated queries
- [ ] Type hints with Pydantic models

**File:** `ai_core/models/llm.py`

```python
class LLMResponse(BaseModel):
    text: str
    tool_calls: List[ToolCall] = []
    confidence: float

class LLM:
    async def generate(self, prompt: str, context: List[Dict]) -> LLMResponse:
        # Call OpenAI API
        # Parse response
        # Return structured response
```

**Tests:** `tests/unit/test_llm.py`

---

**1.2 - Conversation Manager (3 days)**
- [ ] Design conversation schema (in-memory + DB)
- [ ] Context manager class
  - Store turn history
  - Build context from last N turns
  - System prompt management
- [ ] `ai_core/conversation.py`

**File:** `ai_core/conversation.py`

```python
class ConversationContext:
    def __init__(self, user_id: str, max_history: int = 20):
        self.user_id = user_id
        self.history: List[Message] = []
        self.max_history = max_history
    
    async def add_message(self, role: str, content: str):
        # Add to history
        # Trim if exceeds max_history
        # Save to memory
        pass
    
    def get_context(self) -> str:
        # Format history for LLM prompt
        pass
```

**Tests:** `tests/unit/test_conversation.py`

---

**1.3 - Basic Memory Storage (2 days)**
- [ ] SQLite database initialization
- [ ] SQLAlchemy models
  - `Conversation` table
  - `Message` table
  - `Fact` table (user facts/preferences)
- [ ] Database connection pooling
- [ ] Schema migrations setup

**File:** `ai_core/memory/database.py`

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    role TEXT, -- 'user' | 'assistant'
    content TEXT,
    timestamp DATETIME,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);

CREATE TABLE facts (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    key TEXT,
    value TEXT,
    created_at DATETIME
);
```

**Tests:** `tests/unit/test_database.py`

---

### Sprint 2 (Weeks 2-3): Tool System & Conversation Flow
**Focus:** Controlled tool execution, basic conversation loop

#### Tasks

**2.1 - Tool System Framework (3 days)**
- [ ] Tool definition schema
- [ ] Allowlist management
- [ ] Input validation
- [ ] `ai_core/tools/definitions.py`

**File:** `ai_core/tools/definitions.py`

```python
@dataclass
class Tool:
    name: str
    description: str
    params: Dict[str, ParamSpec]
    allowed_inputs: Dict[str, List[str]]  # Whitelist per param
    executor: Callable
    requires_confirmation: bool = False

ALLOWLIST = {
    "search_web": Tool(...),
    "get_time": Tool(...),
    "create_task": Tool(...),
    # More tools to be added in Phase 2-3
}
```

**Tests:** `tests/unit/test_tools.py`

---

**2.2 - Tool Executor & Validator (2 days)**
- [ ] Validation pipeline
- [ ] Safe execution wrapper
- [ ] Result formatting
- [ ] `ai_core/tools/executor.py`

**File:** `ai_core/tools/executor.py`

```python
class ToolExecutor:
    async def execute(self, tool_name: str, params: Dict) -> ToolResult:
        # 1. Check allowlist
        # 2. Validate inputs
        # 3. Check permissions
        # 4. Execute tool
        # 5. Log action
        # 6. Return result
        pass
```

**Tests:** `tests/integration/test_tool_executor.py`

---

**2.3 - Main Conversation Loop (3 days)**
- [ ] FastAPI endpoint for chat
- [ ] Request/response models
- [ ] Full flow: input → LLM → tools → response
- [ ] `ai_core/main.py` (FastAPI app)
- [ ] `ai_core/planner/planner.py` (task planning)

**File:** `ai_core/main.py`

```python
@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Get conversation context
    # 2. Call LLM
    # 3. Parse response
    # 4. Execute tools if needed
    # 5. Return response
    pass

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept connection
    # Listen for messages
    # Process & respond
    pass
```

**Tests:** `tests/integration/test_conversation_flow.py`

---

### Sprint 3 (Weeks 3-4): Sync System & Voice I/O
**Focus:** Android ↔ PC sync, voice basics

#### Tasks

**3.1 - Sync Engine Foundation (3 days)**
- [ ] Sync message format
- [ ] Change tracking (in database)
- [ ] Conflict detection
- [ ] `sync/sync_engine.py`

**File:** `sync/sync_engine.py`

```python
class SyncEngine:
    async def sync_from_android(self, changes: List[Change]) -> SyncResult:
        # Apply changes to PC DB
        # Detect conflicts
        # Return result
        pass
    
    async def sync_to_android(self, since: DateTime) -> List[Change]:
        # Get changes since timestamp
        # Format for Android
        # Return changes
        pass
```

**Tests:** `tests/integration/test_sync.py`

---

**3.2 - Voice I/O Wrapper (2 days)**
- [ ] OpenAI Whisper integration
- [ ] Edge TTS integration
- [ ] `voice/stt.py` and `voice/tts.py`

**File:** `voice/stt.py`

```python
class SpeechToText:
    async def transcribe(self, audio_file: BinaryIO) -> str:
        # Send to Whisper API
        # Return transcribed text
        pass
```

**File:** `voice/tts.py`

```python
class TextToSpeech:
    async def speak(self, text: str) -> BinaryIO:
        # Generate speech
        # Return audio file
        pass
```

**Tests:** `tests/unit/test_voice.py`

---

**3.3 - WebSocket Sync Server (2 days)**
- [ ] WebSocket endpoint in FastAPI
- [ ] Message handling
- [ ] Connection management
- [ ] Offline queue on PC side

**File:** `sync/sync_server.py`

```python
@app.websocket("/ws")
async def sync_websocket(websocket: WebSocket):
    # Handle Android connections
    # Receive sync messages
    # Process changes
    # Send updates back
    pass
```

---

### Sprint 4 (Week 4-5): Android App - Phase 1
**Focus:** Minimal functional UI

#### Tasks

**4.1 - Android Project Setup (1 day)**
- [ ] Create Kotlin/Jetpack Compose project
- [ ] Set up dependencies
- [ ] Create project structure

**4.2 - Local Database (SQLite - Room) (2 days)**
- [ ] Room entities for tasks, conversations
- [ ] DAO interfaces
- [ ] Database initialization

**File:** `android/app/src/main/kotlin/com/jarvis/app/data/`

```kotlin
@Entity
data class Task(
    @PrimaryKey val id: String,
    val title: String,
    val status: String,
    val createdAt: LocalDateTime,
    val localOnly: Boolean = false,
    val syncStatus: String = "pending"
)

@Dao
interface TaskDao {
    @Query("SELECT * FROM task")
    suspend fun getAllTasks(): List<Task>
    
    @Insert
    suspend fun insertTask(task: Task)
}
```

**4.3 - UI Screens - Chat (2 days)**
- [ ] Chat screen (Jetpack Compose)
- [ ] Message list
- [ ] Input field
- [ ] Connect to PC Agent (WebSocket)

**File:** `android/app/src/main/kotlin/com/jarvis/app/ui/ChatScreen.kt`

```kotlin
@Composable
fun ChatScreen(viewModel: ChatViewModel) {
    Column(modifier = Modifier.fillMaxSize()) {
        MessageList(viewModel.messages)
        ChatInput(onSend = { viewModel.sendMessage(it) })
    }
}
```

**4.4 - UI Screens - Tasks (1 day)**
- [ ] Task list screen
- [ ] Task creation
- [ ] Task status display

**4.5 - Offline Queue (1 day)**
- [ ] Local database for offline tasks
- [ ] Queue management
- [ ] Auto-sync when online

---

### Sprint 5 (Week 5-6): Testing & Integration
**Focus:** End-to-end testing, bug fixes

#### Tasks

**5.1 - Unit Tests (2 days)**
- [ ] Test all core components
- [ ] Target 80%+ coverage on critical paths
- [ ] Run: `pytest tests/unit/`

**5.2 - Integration Tests (2 days)**
- [ ] Test full conversation flow
- [ ] Test sync (offline scenarios)
- [ ] Test PC ↔ Android communication
- [ ] Run: `pytest tests/integration/`

**5.3 - Android Tests (1 day)**
- [ ] Unit tests for ViewModels
- [ ] UI tests for screens

**5.4 - Bug Fixes & Refinement (1 day)**
- [ ] Fix issues found in testing
- [ ] Performance optimization
- [ ] Error message improvements

---

## Detailed File Structure (Phase 1)

```
jarvis/
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Pytest configuration
├── setup.py                       # Package setup
│
├── ai_core/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app
│   ├── config.py                 # Configuration loader
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── llm.py               # GPT-4 interface
│   │   └── schemas.py           # Pydantic models
│   │
│   ├── conversation/
│   │   ├── __init__.py
│   │   ├── manager.py           # Conversation context
│   │   └── message.py           # Message handling
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # ORM models
│   │   └── queries.py           # Query functions
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── definitions.py       # Tool specs
│   │   ├── executor.py          # Execution engine
│   │   └── validators.py        # Input validation
│   │
│   └── planner/
│       ├── __init__.py
│       └── planner.py           # Task planning
│
├── voice/
│   ├── __init__.py
│   ├── stt.py                   # Speech-to-Text
│   └── tts.py                   # Text-to-Speech
│
├── sync/
│   ├── __init__.py
│   ├── sync_engine.py           # Sync logic
│   ├── sync_server.py           # WebSocket server
│   └── models.py                # Sync data models
│
├── android/
│   └── app/
│       └── src/main/kotlin/com/jarvis/app/
│           ├── MainActivity.kt
│           ├── ui/
│           │   ├── ChatScreen.kt
│           │   ├── TaskScreen.kt
│           │   └── theme/
│           ├── data/
│           │   ├── local/
│           │   │   ├── TaskDao.kt
│           │   │   └── AppDatabase.kt
│           │   └── remote/
│           │       └── PcAgentClient.kt
│           └── viewmodel/
│               ├── ChatViewModel.kt
│               └── TaskViewModel.kt
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   ├── test_llm.py
│   │   ├── test_conversation.py
│   │   ├── test_memory.py
│   │   ├── test_tools.py
│   │   └── test_voice.py
│   └── integration/
│       ├── test_conversation_flow.py
│       ├── test_tool_executor.py
│       ├── test_sync.py
│       └── test_pc_to_android.py
│
├── docs/
│   ├── architecture.md           # ✅ Created
│   ├── roadmap.md               # ✅ Created
│   ├── setup.md                 # ✅ Created
│   ├── decisions.md             # ✅ Created
│   └── PHASE_1_IMPLEMENTATION.md # This file
│
├── config/
│   └── .env.example             # ✅ Created
│
├── README.md                     # ✅ Created
├── AGENTS.md                     # ✅ Created
├── .gitignore                    # ✅ Created
└── requirements.txt              # To be created
```

---

## Requirements.txt (Phase 1)

```
# Core
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.0

# HTTP & WebSocket
aiohttp==3.9.1
websockets==12.0

# AI/LLM
openai==1.3.0
tiktoken==0.5.2

# Audio
pydub==0.25.1

# Logging
python-json-logger==2.0.7

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Development
black==23.12.0
pylint==3.0.3
mypy==1.7.1
isort==5.13.2
```

---

## Development Workflow - Phase 1

### Daily Standup Questions
- What did I complete yesterday?
- What am I working on today?
- Any blockers?

### PR Review Checklist
- [ ] Tests pass (80%+ coverage)
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] Code follows style guide (black, pylint)
- [ ] Type hints present for public APIs
- [ ] Commit messages clear

### Definition of Done (Per Feature)
- Code implemented
- Unit tests written & passing
- Integration tests passing
- Documentation updated
- Code reviewed & approved
- Merged to main

---

## Known Risks & Mitigations (Phase 1)

| Risk | Impact | Mitigation |
|------|--------|-----------|
| OpenAI API costs spike | Budget | Implement caching, monitor usage, fallback model |
| WebSocket connection issues | UX | Implement reconnection logic, fallback to REST |
| SQLite concurrency | Data corruption | Use WAL mode, connection pooling |
| LLM hallucination (tool calls) | Security | Strict allowlist, input validation, testing |
| Android sync bugs | Data loss | Comprehensive sync tests, audit logging |
| Voice quality | UX | Test Whisper accuracy, implement retries |

---

## Success Metrics (Phase 1 End)

- ✅ **Functional:** JARVIS responds to text & voice input
- ✅ **Reliable:** 95%+ tool execution success rate
- ✅ **Tested:** 80%+ code coverage
- ✅ **Fast:** Response latency <2s (most queries)
- ✅ **Synced:** 0 data loss in offline/online scenarios
- ✅ **Usable:** Android app works intuitively

---

## Next: Phase 2 Preview

After Phase 1 completes:
- Browser integration (Firefox automation)
- Advanced vision (screenshot analysis)
- Enhanced Android UI
- PC Dashboard v0.1

---

## Getting Started

To begin Phase 1 development:

1. **Setup environment** (see `docs/setup.md`)
2. **Sprint 1 kickoff** - Start with LLM integration
3. **Create issues** - Break down tasks into concrete PRs
4. **Daily commits** - Push progress daily
5. **Weekly reviews** - Adjust plan based on learnings

---

Last updated: 2026-09-25
