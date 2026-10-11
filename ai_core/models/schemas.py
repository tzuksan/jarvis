"""Pydantic models for request/response schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Represents a tool call request from LLM"""
    
    name: str = Field(..., description="Tool name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    confidence: float = Field(default=1.0, description="Confidence score (0-1)")


class LLMResponse(BaseModel):
    """LLM response with text and optional tool calls"""
    
    text: str = Field(..., description="Response text")
    tool_calls: List[ToolCall] = Field(
        default_factory=list, 
        description="List of tool calls to execute"
    )
    confidence: float = Field(default=1.0, description="Overall confidence score")
    model: str = Field(default="gpt-4-turbo-preview", description="Model used")
    tokens_used: int = Field(default=0, description="Tokens consumed")


class Message(BaseModel):
    """Single message in conversation"""
    
    role: str = Field(..., description="Role: 'user' | 'assistant' | 'system'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: List[ToolCall] = Field(default_factory=list)


class ConversationContext(BaseModel):
    """Context for a conversation"""
    
    conversation_id: str = Field(..., description="Unique conversation ID")
    user_id: str = Field(..., description="User ID")
    messages: List[Message] = Field(default_factory=list, description="Message history")
    system_prompt: str = Field(
        default="You are JARVIS, a helpful AI assistant. Be concise and direct.",
        description="System prompt for LLM"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Chat request from client"""
    
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message")
    include_tools: bool = Field(default=True, description="Allow tool calls")


class ChatResponse(BaseModel):
    """Chat response to client"""
    
    conversation_id: str
    response: str = Field(..., description="Assistant response")
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tokens_used: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
