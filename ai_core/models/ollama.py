"""Ollama LLM Provider - Local, Privacy-First"""

import json
import logging
from typing import List, Optional

import httpx

from .base import LLMProvider
from .schemas import LLMResponse, Message

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local model execution
    
    Ollama runs on localhost and provides a simple HTTP API.
    Perfect for privacy-first, offline-capable JARVIS.
    
    Requirements:
        - Ollama installed: https://ollama.ai
        - Running locally: ollama serve
        - Model pulled: ollama pull mistral (or your choice)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout_seconds: int = 60,
    ):
        """Initialize Ollama provider
        
        Args:
            base_url: Ollama API base URL (default: localhost:11434)
            model: Model name (default: mistral)
            temperature: Creativity level (default: 0.7)
            max_tokens: Max response length (default: 2000)
            timeout_seconds: API timeout (default: 60)
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout_seconds,
                base_url=self.base_url,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        tools_available: bool = False,
    ) -> LLMResponse:
        """Generate response using Ollama
        
        Args:
            messages: Conversation history
            system_prompt: System message
            tools_available: Enable tool calling (Phase 2)
            
        Returns:
            LLMResponse
            
        Raises:
            ValueError: If Ollama is unavailable or API error
        """
        try:
            # Build message list
            api_messages = []
            
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            
            for msg in messages:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
            
            logger.debug(f"Calling Ollama API ({self.model}) at {self.base_url}...")
            
            # Call Ollama API
            client = await self._get_client()
            response = await client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": api_messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
            )
            
            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Ollama API error {response.status_code}: {error_text}")
                raise ValueError(f"Ollama API error: {response.status_code}")
            
            data = response.json()
            
            self._call_count += 1
            # Ollama doesn't return token counts by default
            # Estimate based on message length (rough approximation)
            estimated_tokens = sum(len(m["content"].split()) for m in api_messages) + len(
                data.get("message", {}).get("content", "").split()
            )
            self._token_count += estimated_tokens
            
            response_text = data.get("message", {}).get("content", "")
            
            return LLMResponse(
                text=response_text,
                tool_calls=[],  # Phase 2: Parse function calls from response
                model=self.model,
                tokens_used=estimated_tokens,
                confidence=0.9,  # Ollama responses are generally reliable
            )
            
        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            raise ValueError(
                f"Cannot connect to Ollama. Make sure it's running: "
                f"ollama serve. URL: {self.base_url}"
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")
            raise ValueError(f"Ollama HTTP error: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Invalid Ollama response format: {e}")
            raise ValueError(f"Invalid Ollama response: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

