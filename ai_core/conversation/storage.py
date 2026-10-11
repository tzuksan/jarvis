"""
Conversation Storage
====================

Abstract interface für Conversation Persistierung.

Später: SQLite, PostgreSQL, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from ai_core.conversation.models import (
    ConversationSession,
    ConversationMessage,
)


class ConversationStorage(ABC):
    """
    Abstract interface für Conversation Persistierung
    
    Implementierungen:
    - SQLiteConversationStorage
    - PostgresConversationStorage (Phase 2+)
    - InMemoryConversationStorage (Testing)
    """
    
    @abstractmethod
    async def save_session(self, session: ConversationSession) -> bool:
        """Speichere eine Session"""
        pass
    
    @abstractmethod
    async def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Lade eine Session"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Lösche eine Session"""
        pass
    
    @abstractmethod
    async def list_sessions(self) -> List[Dict]:
        """Liste alle Sessions auf"""
        pass
    
    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        message: ConversationMessage
    ) -> bool:
        """Speichere eine einzelne Nachricht"""
        pass
    
    @abstractmethod
    async def load_messages(self, session_id: str) -> List[ConversationMessage]:
        """Lade alle Nachrichten einer Session"""
        pass
    
    @abstractmethod
    async def clear_session_messages(self, session_id: str) -> bool:
        """Lösche alle Nachrichten einer Session"""
        pass


class InMemoryConversationStorage(ConversationStorage):
    """
    In-Memory Storage für Tests
    
    Alles in RAM - keine Persistierung!
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    async def save_session(self, session: ConversationSession) -> bool:
        self.sessions[session.session_id] = session
        return True
    
    async def load_session(self, session_id: str) -> Optional[ConversationSession]:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def list_sessions(self) -> List[Dict]:
        return [
            {
                "session_id": session.session_id,
                "title": session.title,
                "message_count": session.message_count(),
                "created_at": session.created_at.isoformat(),
            }
            for session in self.sessions.values()
        ]
    
    async def save_message(
        self,
        session_id: str,
        message: ConversationMessage
    ) -> bool:
        session = self.sessions.get(session_id)
        if session:
            session.messages.append(message)
            session.updated_at = datetime.now()
            return True
        return False
    
    async def load_messages(self, session_id: str) -> List[ConversationMessage]:
        session = self.sessions.get(session_id)
        return session.messages if session else []
    
    async def clear_session_messages(self, session_id: str) -> bool:
        session = self.sessions.get(session_id)
        if session:
            session.messages.clear()
            session.updated_at = datetime.now()
            return True
        return False


if __name__ == "__main__":
    import asyncio
    
    async def test():
        storage = InMemoryConversationStorage()
        
        # Test save/load
        session = ConversationSession(session_id="test-1")
        session.add_message("system", "You are helpful")
        session.add_message("user", "Hello!")
        
        await storage.save_session(session)
        
        loaded = await storage.load_session("test-1")
        print(f"Loaded session: {loaded.title if loaded else None}")
        print(f"Messages: {loaded.message_count() if loaded else 0}")
    
    asyncio.run(test())
