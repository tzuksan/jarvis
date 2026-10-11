"""Abstract base class for LLM providers"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .schemas import LLMResponse, Message


class LLMProvider(ABC):
    """Abstract base class for LLM providers
    
    All LLM providers (OpenAI, Ollama, Anthropic, etc.) must implement this interface.
    This ensures JARVIS remains provider-agnostic.
    """

    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout_seconds: int = 60,
    ):
        """Initialize LLM provider
        
        Args:
            model: Model name/identifier
            temperature: Creativity level (0-1)
            max_tokens: Maximum response length
            timeout_seconds: API timeout
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self._call_count = 0
        self._token_count = 0

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        tools_available: bool = False,
    ) -> LLMResponse:
        """Generate LLM response
        
        Args:
            messages: Conversation history
            system_prompt: System message (optional)
            tools_available: Enable tool/function calling
            
        Returns:
            LLMResponse with text and optional tool calls
            
        Raises:
            ValueError: If API error occurs
        """
        pass

    @property
    def stats(self) -> Dict[str, int]:
        """Get usage statistics"""
        return {
            "call_count": self._call_count,
            "total_tokens": self._token_count,
            "avg_tokens_per_call": (
                self._token_count // self._call_count
                if self._call_count > 0
                else 0
            ),
        }

    def reset_stats(self) -> None:
        """Reset usage statistics"""
        self._call_count = 0
        self._token_count = 0

    def get_provider_name(self) -> str:
        """Get provider name (e.g., 'openai', 'ollama')"""
        return self.__class__.__name__.replace("Provider", "").lower()

    def get_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": self.get_provider_name(),
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stats": self.stats,
        }
