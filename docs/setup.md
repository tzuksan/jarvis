# JARVIS Setup & Development Guide

## System Requirements

### Windows PC (Server)
- **OS:** Windows 10 21H2 or Windows 11
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 20GB free (SSD preferred)
- **Python:** 3.11 or later
- **GPU:** Optional (speeds up vision tasks)

### Android (Client)
- **OS:** Android 10 or later
- **RAM:** 4GB minimum (6GB+ recommended)
- **Storage:** 100MB free
- **Android Studio:** For development

### Network
- LAN: Windows & Android on same network (Phase 1)
- Internet: Required for LLM APIs, optional for offline features (Phase 4+)

---

## Windows Development Setup

### 1. Prerequisites

```powershell
# Check Python version
python --version    # Should be 3.11+

# Install git if needed
# Download from https://git-scm.com/download/win

# Install FFmpeg (needed for audio processing)
# Via Chocolatey:
choco install ffmpeg

# Or via scoop:
scoop install ffmpeg
```

### 2. Clone Repository

```bash
git clone https://github.com/tzuksan/jarvis.git
cd jarvis
```

### 3. Create Virtual Environment

```powershell
# Create venv
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# Or CMD
venv\Scripts\activate.bat
```

### 4. Install Dependencies (Phase 1)

```bash
pip install -r requirements.txt
```

**Early requirements.txt (Phase 1):**
```
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
pydantic==2.5.0
sqlalchemy==2.0.23
openai==1.3.0
pydantic-ai==0.1.0
websockets==12.0
```

### 5. Configure Environment

```bash
# Copy template
copy config\.env.example .env

# Edit .env
# Add your API keys:
# OPENAI_API_KEY=sk-...
# WHISPER_API_KEY=...
```

### 6. Run Tests

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# All tests
pytest
```

### 7. Start PC Agent

```bash
# Development mode (with auto-reload)
uvicorn ai_core.main:app --reload --port 8000

# Production mode
uvicorn ai_core.main:app --port 8000
```

The PC Agent runs on `ws://localhost:8000/ws`

---

## Android Development Setup

### 1. Prerequisites

- Install Android Studio (latest version)
- Android SDK 34+
- Android Emulator or physical device (Android 10+)

### 2. Open Project

```bash
cd android
```

Open in Android Studio.

### 3. Sync Dependencies

In Android Studio:
- File → Sync Now

### 4. Configure Local Connection

Edit `android/app/build.gradle`:

```gradle
buildTypes {
    debug {
        // PC Agent connection (debug build)
        buildConfigField "String", "PC_AGENT_URL", "\"ws://192.168.1.100:8000\""
    }
    release {
        // PC Agent connection (production)
        buildConfigField "String", "PC_AGENT_URL", "\"wss://jarvis.example.com\""
    }
}
```

### 5. Run on Emulator or Device

```bash
# Ensure PC Agent is running
# Then run Android app from Android Studio
```

**For emulator to access host PC:**
- Use `10.0.2.2` instead of `localhost`
- Configure firewall to allow port 8000

---

## Database Setup (SQLite - Phase 1)

```bash
# Database is auto-created on first run
# Location: jarvis_data.db

# To reset (development only):
rm jarvis_data.db
```

Schema is managed via SQLAlchemy migrations.

---

## API Keys & Secrets

**NEVER commit `.env` to git!**

### Required APIs (Phase 1)

1. **OpenAI (Conversation + Vision)**
   - Get key: https://platform.openai.com/api-keys
   - Model: gpt-4-turbo-preview

2. **Whisper API (Speech-to-Text)**
   - Same OpenAI account
   - Model: whisper-1

3. **Text-to-Speech** (Edge TTS - no key needed initially)

### Example .env

```env
# LLM
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview

# Voice
WHISPER_API_KEY=sk-...
TTS_PROVIDER=edge_tts

# Database
DATABASE_URL=sqlite:///jarvis_data.db

# Dev
DEBUG=True
LOG_LEVEL=DEBUG
```

---

## Project Structure (Phase 1)

```
jarvis/
├── README.md
├── AGENTS.md
├── requirements.txt
├── .env.example
│
├── ai_core/                    # Core AI logic
│   ├── __init__.py
│   ├── main.py                # FastAPI app
│   ├── config.py              # Configuration
│   ├── models/                # LLM wrappers
│   │   ├── llm.py            # GPT-4 interface
│   │   └── vision.py          # Vision model
│   ├── planner/               # Task planning
│   │   └── planner.py
│   ├── memory/                # Memory system
│   │   ├── database.py       # SQLite wrapper
│   │   └── memory.py         # Query interface
│   └── tools/                 # Tool system
│       ├── definitions.py     # Tool specs
│       └── executor.py        # Execution + validation
│
├── android/                    # Android app
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── kotlin/
│   │   │   │   │   └── com/jarvis/app/
│   │   │   │   │       ├── MainActivity.kt
│   │   │   │   │       ├── ui/
│   │   │   │   │       ├── data/
│   │   │   │   │       └── util/
│   │   │   │   └── res/
│   │   │   └── test/
│   │   └── build.gradle
│   └── gradle.properties
│
├── sync/                       # Sync engine
│   ├── sync_server.py         # WebSocket server
│   └── sync_engine.py         # Sync logic
│
├── voice/                      # Voice I/O
│   ├── stt.py                # Speech-to-Text
│   └── tts.py                # Text-to-Speech
│
├── tests/
│   ├── unit/
│   │   ├── test_llm.py
│   │   ├── test_memory.py
│   │   └── test_tools.py
│   ├── integration/
│   │   └── test_sync.py
│   └── conftest.py           # Pytest fixtures
│
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── setup.md (this file)
│   └── decisions.md
│
└── config/
    └── .env.example
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feat/conversation-system
```

### 2. Make Changes

- Follow code style (see below)
- Write tests
- Update docs if needed

### 3. Run Tests

```bash
pytest tests/

# Or specific tests
pytest tests/unit/test_llm.py -v
```

### 4. Commit

```bash
git add .
git commit -m "Add conversation system

- Implement LLM context manager
- Add memory integration
- Handle multi-turn conversations

Resolves #123"
```

### 5. Push & Create PR

```bash
git push origin feat/conversation-system
```

Then create PR on GitHub.

---

## Code Style & Standards

### Python (ai_core, sync, voice)

- **Formatter:** Black (line length: 100)
- **Linter:** pylint
- **Type hints:** Required for public APIs
- **Docstrings:** Google style for classes & functions

```bash
# Format code
black ai_core/ sync/ voice/

# Lint
pylint ai_core/ sync/ voice/

# Type check
mypy ai_core/
```

### Kotlin (Android)

- **Style:** Google Kotlin Style Guide
- **Formatter:** Android Studio built-in
- **Architecture:** MVVM with Jetpack Compose

### Git Commits

```
Type: Short description (50 chars)

Longer explanation (wrap at 72 chars)
- Point 1
- Point 2

Resolves #issue_number
```

**Types:** feat, fix, docs, style, refactor, test, chore

---

## Testing Strategy

### Unit Tests (test_*.py)

```python
import pytest
from ai_core.memory import Memory

def test_memory_store_and_retrieve():
    mem = Memory()
    mem.store("key", "value")
    assert mem.retrieve("key") == "value"
```

Run: `pytest tests/unit/`

### Integration Tests

```python
def test_full_conversation_flow():
    # Test LLM + Memory + Tools together
    pass
```

Run: `pytest tests/integration/`

### Coverage Target

- Minimum 80% for critical components
- Run: `pytest --cov=ai_core`

---

## Debugging

### Enable Debug Mode

In `.env`:
```
DEBUG=True
LOG_LEVEL=DEBUG
```

### Logs

Logs are written to:
- Console (development)
- `logs/jarvis.log` (all modes)

### Python Debugger

```python
import pdb; pdb.set_trace()

# Or in pytest
pytest --pdb
```

### Android Debugging

- Use Android Studio Debugger
- Logcat for log output
- Database Inspector (SQLite Browser)

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'ai_core'"

**Solution:**
```bash
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -e .
```

### Issue: "Connection refused" from Android to PC

**Solution:**
- Ensure PC Agent is running on port 8000
- Check Windows Firewall allows port 8000
- On emulator, use `10.0.2.2` instead of `localhost`

### Issue: "API key not found"

**Solution:**
- Copy `.env.example` to `.env`
- Add your OpenAI API key
- Restart app

---

## Performance Tips

### Python (PC Agent)
- Use async/await for I/O operations
- Cache LLM responses when possible
- Profile with cProfile: `python -m cProfile -s cumtime main.py`

### Android
- Use coroutines for network operations
- Implement pagination for large lists
- Monitor memory with Android Profiler

### Database
- Add indexes for frequently queried fields
- Use connection pooling
- Archive old logs regularly

---

## Deployment (Future)

For Phase 4+ deployments:
- Use Docker for PC Agent
- Deploy to VPS or home server
- Set up HTTPS with Let's Encrypt
- Use PostgreSQL instead of SQLite
- Implement proper backups

---

## Getting Help

1. Check existing issues: https://github.com/tzuksan/jarvis/issues
2. Review documentation
3. Run tests to isolate problems
4. Check logs for error messages
5. Create new issue with:
   - OS & version
   - Python/Android version
   - Error message (full stack trace)
   - Steps to reproduce

---

## Next Steps

1. **Complete Phase 1 Setup:** Get conversation system running
2. **Write First Tests:** Ensure code quality from start
3. **Setup CI/CD:** GitHub Actions for automated testing
4. **Start Phase 1 Development:** Follow roadmap.md

---

Last updated: 2026-09-25
