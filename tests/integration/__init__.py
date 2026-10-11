"""
Integration Tests for JARVIS
=============================

Integration tests test REAL external services (Ollama, Firefox, OBS, etc.)

Unlike unit tests that mock everything, integration tests:
- Actually connect to services
- Verify real behavior
- Help debug real issues
- Are skipped if services unavailable

Folder structure:
tests/integration/
├── test_ollama_integration.py    - Real Ollama API tests
├── test_browser_integration.py   - Real Firefox tests
├── test_obs_integration.py       - Real OBS tests
├── test_sync_integration.py      - Real Sync tests
└── __init__.py
"""
