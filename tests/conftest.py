"""Test fixtures and configuration for pytest"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch

from ai_core.config import Settings
from ai_core.models.schemas import Message, ToolCall, LLMResponse


@pytest.fixture
def settings():
    """Provide test settings"""
    return Settings(
        openai_api_key="sk-test-key-12345",
        openai_model="gpt-4-turbo-preview",
        debug=True,
        log_level="DEBUG",
    )


@pytest.fixture
def sample_messages():
    """Provide sample conversation messages"""
    return [
        Message(role="user", content="Hello, what time is it?"),
        Message(role="assistant", content="I don't have access to the current time right now."),
        Message(role="user", content="Can you help me create a task?"),
    ]


@pytest.fixture
def sample_llm_response():
    """Provide sample LLM response"""
    return LLMResponse(
        text="I'd be happy to help you create a task. What would you like the task to be?",
        tool_calls=[],
        model="gpt-4-turbo-preview",
        tokens_used=42,
    )


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.content = "Test response"
    response.choices[0].message.tool_calls = None
    response.usage = Mock()
    response.usage.total_tokens = 42
    return response


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client
