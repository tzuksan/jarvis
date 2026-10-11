# JARVIS - Personal AI Assistant

A modular, secure, and extensible personal AI assistant for Windows and Android.

## Vision

JARVIS is a **real assistant**, not just a chatbot. It understands context, asks clarifying questions when needed, and autonomously executes tasks across multiple platforms.

### Example

**User:** "I want to stream."  
**JARVIS:** "On which platform? YouTube, Twitch, or both?"  
**User:** "Both."  
**JARVIS:** *[Only asks for missing information, then executes the required actions]*

## Key Features

- 🧠 Natural language understanding with context awareness
- 🎤 Voice input/output (Speech-to-Text, Text-to-Speech)
- 📱 Windows & Android synchronization (bidirectional)
- 🔧 Controlled tool system with security validation
- 💾 Persistent memory across sessions
- 🖥️ PC control & automation (programs, files, system info)
- 🌐 Web browsing & research (Firefox integration)
- 📹 OBS streaming control
- 👁️ Screen analysis & vision capabilities
- ⚡ Works offline on Android when PC is unavailable

## Architecture

```
┌─────────────────────────────────────────────────┐
│              JARVIS AI Core                      │
│  (Planner, Memory, Tool System, Models)         │
└────────────┬────────────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────────┐    ┌──────────────┐
│  Windows PC │    │  Android App │
│  Dashboard  │◄──►│   Mobile UI  │
└─────────────┘    └──────────────┘
```

## Repository Structure

```
jarvis/
├── README.md
├── AGENTS.md
├── .gitignore
│
├── docs/
│   ├── architecture.md      # System design
│   ├── roadmap.md          # Development phases
│   ├── setup.md            # Setup & contribution guide
│   └── decisions.md        # Architecture decisions (ADR)
│
├── ai-core/                # Core AI logic
│   ├── planner/           # Task planning
│   ├── memory/            # Memory system
│   ├── models/            # LLM integrations
│   └── tools/             # Tool definitions & validation
│
├── android/                # Android app
│   └── app/
│
├── pc-agent/               # Windows agent/service
│   └── src/
│
├── browser-agent/          # Firefox automation
│
├── vision/                 # Screenshot analysis
│
├── voice/                  # Speech I/O
│   ├── stt/               # Speech-to-Text
│   └── tts/               # Text-to-Speech
│
├── sync/                   # Sync engine
│
├── tests/                  # Tests
│
└── config/
    └── .env.example       # Environment template
```

## Getting Started

See [`docs/setup.md`](docs/setup.md) for detailed setup instructions.

### Quick Start (Development)

```bash
# Clone and navigate
cd jarvis

# Install dependencies
# (See docs/setup.md for platform-specific instructions)

# Run tests
# (Commands depend on components)

# Start development
# (See individual component READMEs)
```

## Development Rules

1. **Analyze before modifying** - Read existing docs and code first
2. **Modular design** - Keep components independent
3. **Security first** - Validate all LLM outputs, use allowlist for tools
4. **No secrets in code** - Use `.env` for sensitive data
5. **Test important functions** - Run tests after changes
6. **Document decisions** - Update `docs/decisions.md` for architectural changes
7. **Avoid monolithic files** - Keep files focused and reasonable in size
8. **Current, stable libraries** - No experimental or unmaintained dependencies

See [`docs/decisions.md`](docs/decisions.md) for architectural decisions.

## Phases

### Phase 1 (Foundation)
- Project setup & structure
- Basic conversation system
- Memory storage
- Android/PC sync foundation

### Phase 2 (Core Abilities)
- Vision (screenshot analysis)
- Speech I/O
- Browser integration

### Phase 3 (Automation)
- PC program control
- OBS integration
- Advanced planning

### Phase 4 (Polish & Scale)
- Dashboards
- Performance optimization
- Advanced memory/learning

See [`docs/roadmap.md`](docs/roadmap.md) for detailed roadmap.

## Contributing

1. Read [`docs/setup.md`](docs/setup.md)
2. Create a feature branch
3. Make focused changes
4. Run tests
5. Commit with clear messages
6. Submit PR

## License

[To be determined]

## Status

🟡 **In Early Development** - Foundation phase (Phase 1) in progress
