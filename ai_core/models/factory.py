"""LLM Provider Factory - Creates the appropriate provider based on configuration"""

import logging
from typing import Optional

from ai_core.config import get_settings

from .base import LLMProvider
from .ollama import OllamaProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM providers
    
    This ensures JARVIS can dynamically switch between providers
    based on configuration, without changing application code.
    """

    _PROVIDERS = {
        "ollama": OllamaProvider,
        # "openai": None,  # Loaded dynamically if openai package available
        # "anthropic": AnthropicProvider,  # Phase 2+
        # "local": LocalProvider,  # Phase 4+ (llama.cpp, etc.)
    }

    @staticmethod
    def _load_optional_providers():
        """Load optional providers that require external packages"""
        try:
            from .openai import OpenAIProvider
            LLMFactory._PROVIDERS["openai"] = OpenAIProvider
            logger.debug("OpenAI provider available (openai package installed)")
        except ImportError:
            logger.debug("OpenAI provider not available (install with: pip install openai)")

    @staticmethod
    def create(settings: Optional[object] = None) -> LLMProvider:
        """Create LLM provider based on settings
        
        Args:
            settings: Settings object (default: load from get_settings())
            
        Returns:
            Configured LLM provider instance
            
        Raises:
            ValueError: If provider not found or misconfigured
        """
        # Ensure optional providers are loaded
        if "openai" not in LLMFactory._PROVIDERS or LLMFactory._PROVIDERS["openai"] is None:
            LLMFactory._load_optional_providers()
        
        if settings is None:
            settings = get_settings()
        
        provider_name = settings.llm_provider.lower()
        logger.info(f"Creating LLM provider: {provider_name}")
        
        if provider_name not in LLMFactory._PROVIDERS:
            available = ", ".join(LLMFactory._PROVIDERS.keys())
            raise ValueError(
                f"Unknown LLM provider: {provider_name}. "
                f"Available providers: {available}"
            )
        
        provider_class = LLMFactory._PROVIDERS[provider_name]
        
        if provider_class is None:
            raise ValueError(
                f"Provider '{provider_name}' is not available. "
                f"Please install the required package."
            )
        
        # Create provider-specific instance
        if provider_name == "ollama":
            provider = provider_class(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout_seconds=settings.llm_timeout_seconds,
            )
        
        elif provider_name == "openai":
            if not settings.openai_api_key:
                raise ValueError(
                    "OpenAI provider requires openai_api_key in .env"
                )
            provider = provider_class(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                timeout_seconds=settings.llm_timeout_seconds,
            )
        
        else:
            raise ValueError(f"Provider {provider_name} not implemented yet")
        
        logger.info(f"LLM provider initialized: {provider.get_info()}")
        return provider

    @staticmethod
    def get_available_providers() -> list:
        """Get list of available provider names"""
        # Load optional providers first
        if "openai" not in LLMFactory._PROVIDERS or LLMFactory._PROVIDERS["openai"] is None:
            LLMFactory._load_optional_providers()
        
        return [name for name, cls in LLMFactory._PROVIDERS.items() if cls is not None]

    @staticmethod
    def register_provider(name: str, provider_class: type) -> None:
        """Register a new provider
        
        This allows external code to add custom providers:
        
        Example:
            LLMFactory.register_provider("custom", MyCustomProvider)
            settings.llm_provider = "custom"
            provider = LLMFactory.create()
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(f"{provider_class} must inherit from LLMProvider")
        
        LLMFactory._PROVIDERS[name.lower()] = provider_class
        logger.info(f"Registered new LLM provider: {name}")

