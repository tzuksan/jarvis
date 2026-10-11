"""
pytest configuration for integration tests
"""

import pytest
import httpx
import asyncio
from typing import Optional

# Ollama availability cache
_ollama_available: Optional[bool] = None
_ollama_model: Optional[str] = None


async def check_ollama_availability() -> bool:
    """
    Check if Ollama is running and responsive
    
    Returns: True if Ollama responds, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except Exception:
        return False


def pytest_configure(config):
    """
    Called after command line options have been parsed
    """
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "ollama: mark test as requiring Ollama service"
    )


@pytest.fixture(scope="session", autouse=True)
def ollama_available():
    """
    Session-level fixture that checks Ollama availability once
    
    This is AUTOUSE, so it runs automatically for every test session.
    It caches the result so we don't spam Ollama with checks.
    """
    global _ollama_available, _ollama_model
    
    # Use asyncio.run() instead of get_event_loop()
    _ollama_available = asyncio.run(check_ollama_availability())
    
    if not _ollama_available:
        print("\n" + "="*70)
        print("⚠️  OLLAMA NOT AVAILABLE")
        print("="*70)
        print("Ollama integration tests will be SKIPPED")
        print("")
        print("To enable integration tests, start Ollama:")
        print("  ollama serve")
        print("")
        print("Ollama URL: http://localhost:11434")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print("✅ OLLAMA IS AVAILABLE")
        print("="*70)
        print("All integration tests will run")
        print("="*70 + "\n")


@pytest.fixture
def requires_ollama():
    """
    Use this fixture in tests that require Ollama
    
    Example:
        def test_something(requires_ollama):
            # This test will only run if Ollama is available
            ...
    """
    if not _ollama_available:
        pytest.skip("Ollama not available - skipping integration test")


@pytest.fixture
def skip_if_no_ollama():
    """
    Alternative name for requires_ollama (more descriptive)
    """
    if not _ollama_available:
        pytest.skip("Ollama not available")
