# Conversation Manager - Quick Reference

**Sprint 1.2 - COMPLETE ✅**

---

## Schnellstart

```python
from ai_core.conversation import (
    ConversationManager,
    MessageRole,
    ConversationContextConfig,
)

# Initialize Manager
config = ConversationContextConfig(
    max_tokens=4000,
    max_messages=50,
    preserve_first_n=2
)
manager = ConversationManager(config)

# Create Session
session_id = manager.create_session("My Chat")
manager.set_active_session(session_id)

# Add Messages
manager.add_message(MessageRole.SYSTEM, "You are helpful")
manager.add_message(MessageRole.USER, "Hello!")

# Get LLM-Ready History
history = manager.get_conversation_history()
# Returns: [{"role": "system", "content": "..."}, ...]

# Manage Context
stats = manager.get_context_stats()
# {"message_count": 2, "token_count": 45, "at_limit": False}
```

---

## API Referenz

### Session Management
```python
# Create
session_id = manager.create_session("Title")

# Get
session = manager.get_session(session_id)

# List all
sessions = manager.list_sessions()

# Set Active
manager.set_active_session(session_id)

# Delete
manager.delete_session(session_id)
```

### Message Management
```python
# Add to active session
manager.add_message(MessageRole.USER, "Content")

# Add to specific session
manager.add_message(
    MessageRole.ASSISTANT,
    "Response",
    session_id="abc123"
)

# Get messages
messages = manager.get_messages(session_id=None)

# Get LLM-ready history
history = manager.get_conversation_history()

# Clear session
manager.clear_session(session_id=None)
```

### Context Management
```python
# Get context stats
stats = manager.get_context_stats()
# {
#     "message_count": 3,
#     "token_count": 120,
#     "message_usage_pct": 6.0,
#     "token_usage_pct": 3.0,
#     "at_limit": False
# }

# Automatic enforcement
# → Triggered on each add_message()
# → Removes oldest messages if over limit
```

### Statistics
```python
# Full stats
stats = manager.get_stats()
# {
#     "total_sessions": 2,
#     "active_session": "abc123",
#     "total_messages": 15,
#     "total_tokens": 2500,
#     "config": {...}
# }
```

---

## Models

### MessageRole Enum
```python
class MessageRole(str, Enum):
    SYSTEM = "system"      # System prompt
    USER = "user"          # User input
    ASSISTANT = "assistant"  # AI response
```

### ConversationMessage
```python
@dataclass
message: ConversationMessage
  role: MessageRole          # SYSTEM, USER, ASSISTANT
  content: str              # Message text
  timestamp: datetime       # When sent
  session_id: Optional[str] # Which session
  metadata: dict           # {confidence, tags, ...}
```

### ConversationSession
```python
@dataclass
session: ConversationSession
  session_id: str
  title: str
  messages: List[ConversationMessage]
  created_at: datetime
  updated_at: datetime
  metadata: dict
  
  methods:
    add_message(role, content)
    get_messages_for_llm() -> List[dict]
    message_count() -> int
    token_estimate() -> int
```

### ConversationContextConfig
```python
@dataclass
config: ConversationContextConfig
  max_tokens: int = 4000              # Limit
  max_messages: int = 50              # Limit
  summarization_threshold: int = 3500 # When to summarize (later)
  preserve_first_n: int = 2           # Never remove first N
```

---

## Integration mit LLM

```python
# 1. Setup
from ai_core.conversation import ConversationManager
from ai_core.models import LLMFactory
from ai_core.config import get_settings

manager = ConversationManager()
settings = get_settings()
provider = LLMFactory.create(settings)

# 2. Create Session
sid = manager.create_session("Chat")
manager.set_active_session(sid)

# 3. Add System Prompt
manager.add_message(
    MessageRole.SYSTEM,
    "You are a helpful assistant"
)

# 4. User Input → Add → Send to LLM
user_input = "What is 2+2?"
manager.add_message(MessageRole.USER, user_input)

# Get history (provider-agnostic format)
history = manager.get_conversation_history()

# Send to any provider (Ollama, OpenAI, etc.)
response = await provider.generate(history)

# 5. Add Response → Auto-manage context
manager.add_message(MessageRole.ASSISTANT, response.text)

# 6. Check context usage
stats = manager.get_context_stats()
if stats["token_usage_pct"] > 80:
    logger.warning("Context 80% full, old messages being removed")
```

---

## Context Limit Strategy

### Automatic Enforcement
When message added and over limit:
```
1. Check message_count > max_messages
   → Remove oldest (except protected)
   
2. Check token_estimate() > max_tokens
   → Remove oldest (except protected)
   
3. Protected (always kept):
   → First preserve_first_n messages
   → Usually: System Prompt + User Message
```

### Example
```python
config = ConversationContextConfig(
    max_messages=3,
    preserve_first_n=1
)
manager = ConversationManager(config)
sid = manager.create_session()
manager.set_active_session(sid)

# Add 5 messages
manager.add_message(MessageRole.SYSTEM, "System")  # Index 0 (protected)
manager.add_message(MessageRole.USER, "Msg1")
manager.add_message(MessageRole.USER, "Msg2")
manager.add_message(MessageRole.USER, "Msg3")
manager.add_message(MessageRole.USER, "Msg4")     # Triggers limit

# Result: Only 3 messages left
# System message is preserved
# Oldest other messages removed
```

---

## Testing

### Run Tests
```bash
pytest tests/unit/test_conversation_manager.py -v

# Expected: 23/23 ✅
```

### Test Coverage
- Message Models (2 tests)
- Session Models (4 tests)
- Manager Operations (9 tests)
- Context Limits (3 tests)
- Multiple Sessions (2 tests)
- Statistics (1 test)
- Storage Interface (1 test)

### Storage Testing
```python
from ai_core.conversation.storage import InMemoryConversationStorage

storage = InMemoryConversationStorage()

# Save
await storage.save_session(session)

# Load
loaded = await storage.load_session(session_id)

# List
sessions = await storage.list_sessions()

# Delete
await storage.delete_session(session_id)
```

---

## Limitations & Future Work

### Current (Phase 1.2)
- ✅ Multiple sessions
- ✅ Message management
- ✅ Context limits (token/message count)
- ✅ In-memory storage
- ⏳ No persistence (yet)

### Planned (Phase 1.3)
- SQLite persistence
- Message summarization
- Real tokenizer per model
- Conversation tagging
- Search/filtering

### Phase 2+
- PostgreSQL backend
- Distributed sessions
- Message encryption
- Conversation analytics

---

## Error Handling

```python
# No active session
try:
    manager.add_message(MessageRole.USER, "Hi")
except ValueError as e:
    print(e)
    # "No active session. Create one first: manager.create_session()"

# Session not found
session = manager.get_session("invalid-id")
# Returns None

# Clear empty session
success = manager.clear_session()
# Returns False if no active session
```

---

## Performance Notes

- **Fast:** O(1) add_message (in-memory)
- **Reasonable:** O(n) context limit enforcement (n=message count)
- **Token estimation:** O(n) (n=message count)
- **Storage:** O(n) per operation (will improve with batch)

For typical conversations (50 messages, 4000 tokens):
- add_message: <1ms
- get_conversation_history: <1ms
- get_context_stats: <1ms

---

**Dokumentation:** See docs/SPRINT_1_2_COMPLETE.md  
**Tests:** See tests/unit/test_conversation_manager.py  
**Code:** See ai_core/conversation/
