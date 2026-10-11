"""OpenAI LLM Provider"""

import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError

from .base import LLMProvider
from .schemas import LLMResponse, Message

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider for cloud-based models
    
    Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
    Requires valid API key in OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout_seconds: int = 60,
    ):
        """Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4-turbo-preview)
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
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        tools_available: bool = False,
    ) -> LLMResponse:
        """Generate response using OpenAI API
        
        Args:
            messages: Conversation history
            system_prompt: System message
            tools_available: Enable tool calling (Phase 2)
            
        Returns:
            LLMResponse
            
        Raises:
            ValueError: If API error occurs
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
            
            logger.debug(f"Calling OpenAI API ({self.model})...")
            
            # Build request
            request_kwargs = {
                "model": self.model,
                "messages": api_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            
            # Add tools if available (Phase 2)
            if tools_available:
                request_kwargs["tools"] = self._get_tool_definitions()

            # Call API
            response = await self.client.chat.completions.create(**request_kwargs)
            
            self._call_count += 1
            self._token_count += response.usage.total_tokens if response.usage else 0
            
            # Parse response
            return self._parse_response(response)
            
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit: {e}")
            raise ValueError(f"OpenAI rate limited: {e}")
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ValueError(f"OpenAI API error: {e}")

    def _parse_response(self, response) -> LLMResponse:
        """Parse OpenAI response into LLMResponse"""
        text = ""
        tool_calls = []
        
        for choice in response.choices:
            if choice.message.content:
                text = choice.message.content
            
            # Handle function calls (Phase 2)
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                for tool_call in choice.message.tool_calls:
                    try:
                        params = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        params = {}
                    
                    from .schemas import ToolCall
                    tool_calls.append(ToolCall(
                        name=tool_call.function.name,
                        params=params,
                    ))
        
        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            model=self.model,
            tokens_used=response.usage.total_tokens if response.usage else 0,
        )

    def _get_tool_definitions(self) -> List:
        """Get tool definitions for function calling (Phase 2)"""
        return []

