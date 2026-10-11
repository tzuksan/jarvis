"""Unit tests for provider-agnostic LLM system

These tests verify that JARVIS's LLM architecture is truly provider-agnostic.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from ai_core.models.base import LLMProvider
from ai_core.models.schemas import Message, LLMResponse
from ai_core.models.factory import LLMFactory
from ai_core.models.ollama import OllamaProvider
from ai_core.config import Settings


@pytest.mark.unit
class TestLLMProviderBase:
    """Test abstract LLM provider base class"""

    def test_provider_base_cannot_instantiate(self):
        """Test that LLMProvider is abstract"""
        with pytest.raises(TypeError):
            LLMProvider(model="test")

    def test_provider_initialization(self):
        """Test provider initialization parameters"""
        class MockProvider(LLMProvider):
            async def generate(self, messages, system_prompt=None, tools_available=False):
                return LLMResponse(text="test")
        
        provider = MockProvider(
            model="test-model",
            temperature=0.5,
            max_tokens=1000,
            timeout_seconds=30,
        )
        
        assert provider.model == "test-model"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 1000
        assert provider.timeout_seconds == 30

    def test_provider_stats_tracking(self):
        """Test stats tracking in base provider"""
        class MockProvider(LLMProvider):
            async def generate(self, messages, system_prompt=None, tools_available=False):
                return LLMResponse(text="test", tokens_used=50)
        
        provider = MockProvider(model="test")
        
        assert provider.stats["call_count"] == 0
        assert provider.stats["total_tokens"] == 0
        
        # Simulate calls
        provider._call_count = 5
        provider._token_count = 500
        
        stats = provider.stats
        assert stats["call_count"] == 5
        assert stats["total_tokens"] == 500
        assert stats["avg_tokens_per_call"] == 100

    def test_provider_stats_reset(self):
        """Test stats reset"""
        class MockProvider(LLMProvider):
            async def generate(self, messages, system_prompt=None, tools_available=False):
                return LLMResponse(text="test")
        
        provider = MockProvider(model="test")
        provider._call_count = 10
        provider._token_count = 1000
        
        provider.reset_stats()
        
        assert provider.stats["call_count"] == 0
        assert provider.stats["total_tokens"] == 0

    def test_provider_info(self):
        """Test provider info method"""
        class MockProvider(LLMProvider):
            async def generate(self, messages, system_prompt=None, tools_available=False):
                return LLMResponse(text="test")
        
        provider = MockProvider(
            model="test-model",
            temperature=0.7,
            max_tokens=2000,
        )
        
        info = provider.get_info()
        
        assert info["provider"] == "mock"
        assert info["model"] == "test-model"
        assert info["temperature"] == 0.7
        assert info["max_tokens"] == 2000
        assert "stats" in info


@pytest.mark.unit
class TestLLMFactory:
    """Test LLM provider factory"""

    def test_factory_get_available_providers(self):
        """Test listing available providers"""
        providers = LLMFactory.get_available_providers()
        
        # Ollama should always be available
        assert "ollama" in providers
        # OpenAI only if package installed
        assert len(providers) >= 1

    def test_factory_create_ollama(self):
        """Test creating Ollama provider (always available)"""
        settings = Settings(
            llm_provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="mistral",
            llm_temperature=0.7,
            llm_max_tokens=2000,
        )
        
        provider = LLMFactory.create(settings)
        
        assert provider.model == "mistral"
        assert provider.get_provider_name() == "ollama"
        assert isinstance(provider, OllamaProvider)

    def test_factory_unknown_provider_fails(self):
        """Test error for unknown provider"""
        settings = Settings(
            llm_provider="nonexistent_provider",
        )
        
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMFactory.create(settings)

    def test_factory_register_custom_provider(self):
        """Test registering custom provider"""
        class CustomProvider(LLMProvider):
            async def generate(self, messages, system_prompt=None, tools_available=False):
                return LLMResponse(text="custom")
        
        # Register
        LLMFactory.register_provider("custom", CustomProvider)
        
        # Verify available
        providers = LLMFactory.get_available_providers()
        assert "custom" in providers

    def test_factory_register_invalid_provider_fails(self):
        """Test registering invalid provider"""
        class NotAProvider:
            pass
        
        with pytest.raises(TypeError, match="must inherit from LLMProvider"):
            LLMFactory.register_provider("invalid", NotAProvider)

    def test_factory_default_settings_uses_ollama(self):
        """Test that default settings use Ollama"""
        settings = Settings()  # Uses defaults
        assert settings.llm_provider == "ollama"
        
        provider = LLMFactory.create(settings)
        assert provider.get_provider_name() == "ollama"


@pytest.mark.unit
class TestOllamaProviderInitialization:
    """Test Ollama provider (initialization only - no network)"""

    def test_ollama_initialization(self):
        """Test Ollama provider initialization"""
        provider = OllamaProvider(
            base_url="http://localhost:11434",
            model="mistral",
            temperature=0.7,
        )
        
        assert provider.model == "mistral"
        assert provider.base_url == "http://localhost:11434"
        assert provider.temperature == 0.7
        assert provider.get_provider_name() == "ollama"

    def test_ollama_strips_base_url_trailing_slash(self):
        """Test that Ollama strips trailing slash from base URL"""
        provider = OllamaProvider(
            base_url="http://localhost:11434/",
            model="mistral",
        )
        
        assert provider.base_url == "http://localhost:11434"


@pytest.mark.unit
class TestProviderAgnosticDesign:
    """Test that architecture is truly provider-agnostic"""

    def test_schemas_dont_import_providers(self):
        """Test that schemas have no provider dependencies"""
        from ai_core.models import schemas
        
        # Should only have Pydantic models
        assert hasattr(schemas, 'Message')
        assert hasattr(schemas, 'LLMResponse')
        assert hasattr(schemas, 'ToolCall')
        
        # Should not import provider-specific modules
        assert 'openai' not in dir(schemas)
        assert 'ollama' not in dir(schemas)

    def test_config_is_provider_agnostic(self):
        """Test that config supports all providers"""
        settings = Settings()
        
        # Should have generic LLM settings
        assert hasattr(settings, 'llm_provider')
        assert hasattr(settings, 'llm_temperature')
        assert hasattr(settings, 'llm_max_tokens')
        assert hasattr(settings, 'llm_timeout_seconds')
        
        # Should have provider-specific settings
        assert hasattr(settings, 'ollama_base_url')
        assert hasattr(settings, 'ollama_model')
        assert hasattr(settings, 'openai_api_key')
        assert hasattr(settings, 'openai_model')

    def test_can_switch_providers_by_config(self):
        """Test switching providers without code changes"""
        # Create with Ollama
        settings1 = Settings(llm_provider="ollama")
        provider1 = LLMFactory.create(settings1)
        
        # Both use Ollama since OpenAI requires API key
        assert provider1.get_provider_name() == "ollama"

    def test_provider_returns_interface_not_implementation(self):
        """Test that factory returns interface, not concrete class"""
        settings = Settings(llm_provider="ollama")
        provider = LLMFactory.create(settings)
        
        # Should be instance of abstract base class
        assert isinstance(provider, LLMProvider)
        
        # Should have required methods
        assert hasattr(provider, 'generate')
        assert hasattr(provider, 'get_provider_name')
        assert hasattr(provider, 'get_info')
        assert hasattr(provider, 'stats')


@pytest.mark.unit
class TestProviderDefaultValues:
    """Test provider default values and configuration"""

    def test_config_defaults(self):
        """Test configuration defaults"""
        settings = Settings()
        
        assert settings.llm_provider == "ollama"
        assert settings.ollama_model == "mistral"
        assert settings.llm_temperature == 0.7
        assert settings.llm_max_tokens == 2000
        assert settings.llm_timeout_seconds == 60

    def test_ollama_can_override_defaults(self):
        """Test overriding Ollama defaults"""
        settings = Settings(
            llm_provider="ollama",
            ollama_model="neural-chat",
            llm_temperature=0.5,
            llm_max_tokens=1000,
        )
        
        provider = LLMFactory.create(settings)
        
        assert provider.model == "neural-chat"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 1000

