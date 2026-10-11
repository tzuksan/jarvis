"""
Conversation Manager Models
============================

Pydantic models für Nachrichten und Conversation Sessions
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Erlaubte Nachrichten-Rollen"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ConversationMessage(BaseModel):
    """
    Eine einzelne Nachricht in einer Conversation
    
    Attributes:
        role: "system", "user" oder "assistant"
        content: Der Nachrichtentext
        timestamp: Wann die Nachricht erstellt wurde
        session_id: Zu welcher Session gehört diese Nachricht
        metadata: Optional: Zusätzliche Daten (z.B. tool_calls, confidence)
    """
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None  # Set by ConversationManager
    metadata: dict = Field(default_factory=dict)  # For extensions
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationSession(BaseModel):
    """
    Eine einzelne Conversation Session mit mehreren Nachrichten
    
    Attributes:
        session_id: Eindeutige ID für diese Session
        title: Kurzer Titel (z.B. "Setup-Fragen")
        messages: Liste der Nachrichten
        created_at: Wann die Session erstellt wurde
        updated_at: Wann die Session zuletzt aktualisiert wurde
        metadata: Optional: Tags, Model-Info, etc.
    """
    session_id: str
    title: str = "Unnamed Conversation"
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)  # For tags, model info, etc.
    
    def add_message(self, role: MessageRole, content: str, metadata: dict = None):
        """Füge eine neue Nachricht zur Session hinzu"""
        message = ConversationMessage(
            role=role,
            content=content,
            session_id=self.session_id,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_messages_for_llm(self) -> List[dict]:
        """
        Konvertiere Nachrichten ins Format für LLM Provider
        
        Format:
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
            ]
        """
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]
    
    def message_count(self) -> int:
        """Anzahl der Nachrichten in dieser Session"""
        return len(self.messages)
    
    def token_estimate(self) -> int:
        """
        Grobe Schätzung der Token (1 Token ≈ 4 Zeichen)
        
        Später: Real tokenizer für spezifisches Modell
        """
        total_chars = sum(len(msg.content) for msg in self.messages)
        return total_chars // 4


class ConversationContextConfig(BaseModel):
    """
    Konfiguration für Context Management
    
    Attributes:
        max_tokens: Maximum Tokens pro Conversation
        max_messages: Maximum Nachrichten pro Conversation
        summarization_threshold: Token-Threshold für Zusammenfassung
        preserve_first_n: Erste N Nachrichten immer behalten
    """
    max_tokens: int = 4000  # Ollama default: 4096
    max_messages: int = 50
    summarization_threshold: int = 3500  # Summarize wenn über 87.5%
    preserve_first_n: int = 2  # Immer System + erste User Message behalten


if __name__ == "__main__":
    # Quick test
    from ai_core.conversation.models import (
        ConversationMessage,
        ConversationSession,
        MessageRole,
    )
    
    # Create a session
    session = ConversationSession(session_id="test-1", title="Test Session")
    
    # Add messages
    session.add_message(MessageRole.SYSTEM, "Du bist ein hilfsbereiter Assistent")
    session.add_message(MessageRole.USER, "Hallo! Was ist 2+2?")
    session.add_message(MessageRole.ASSISTANT, "2+2 = 4")
    
    # Test methods
    print(f"Messages: {session.message_count()}")
    print(f"Estimated tokens: {session.token_estimate()}")
    print(f"LLM format: {session.get_messages_for_llm()}")
