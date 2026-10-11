"""
JARVIS Conversation Management
==============================

Conversation Manager für mehrere parallele Sessions.

Modules:
- models: Pydantic models (ConversationSession, ConversationMessage)
- manager: ConversationManager (Hauptkomponente)
- storage: Abstract storage interface + implementations
"""

from ai_core.conversation.models import (
    ConversationMessage,
    ConversationSession,
    MessageRole,
    ConversationContextConfig,
)
from ai_core.conversation.manager import ConversationManager
from ai_core.conversation.storage import (
    ConversationStorage,
    InMemoryConversationStorage,
)

__all__ = [
    "ConversationMessage",
    "ConversationSession",
    "MessageRole",
    "ConversationContextConfig",
    "ConversationManager",
    "ConversationStorage",
    "InMemoryConversationStorage",
]
