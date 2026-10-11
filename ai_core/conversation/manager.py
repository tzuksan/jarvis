"""
Conversation Manager
====================

Zentrale Komponente für Verwaltung mehrerer Conversation Sessions.

Features:
- Mehrere parallele Sessions
- Nachricht speichern/laden
- Context Limits (Token/Message Count)
- Alte Nachrichten entfernen/zusammenfassen
- Keine Abhängigkeit von spezifischem LLM Provider
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ai_core.conversation.models import (
    ConversationSession,
    ConversationMessage,
    MessageRole,
    ConversationContextConfig,
)

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Verwaltet mehrere Conversation Sessions
    
    Hauptverantwortungen:
    1. Erstelle/lade Sessions
    2. Verwalte Nachrichten
    3. Enforce Context Limits
    4. Persistiere zu Storage (later)
    """
    
    def __init__(self, config: Optional[ConversationContextConfig] = None):
        """
        Initialize ConversationManager
        
        Args:
            config: Context-Limits und Verhaltensweise
        """
        self.config = config or ConversationContextConfig()
        self.sessions: Dict[str, ConversationSession] = {}
        self.active_session_id: Optional[str] = None
        logger.info(
            f"ConversationManager initialized with "
            f"max_tokens={self.config.max_tokens}, "
            f"max_messages={self.config.max_messages}"
        )
    
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    def create_session(self, title: str = "Unnamed Conversation") -> str:
        """
        Erstelle eine neue Conversation Session
        
        Args:
            title: Beschreibung der Session
            
        Returns:
            session_id: Die neue Session-ID
            
        Example:
            manager = ConversationManager()
            session_id = manager.create_session("Setup-Fragen")
        """
        session_id = str(uuid.uuid4())[:8]  # Kurze ID
        session = ConversationSession(session_id=session_id, title=title)
        self.sessions[session_id] = session
        
        logger.info(f"Created session: {session_id} ({title})")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Lade eine Session"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[dict]:
        """Liste alle Sessions auf"""
        return [
            {
                "session_id": session.session_id,
                "title": session.title,
                "message_count": session.message_count(),
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            }
            for session in self.sessions.values()
        ]
    
    def set_active_session(self, session_id: str) -> bool:
        """Setze aktive Session"""
        if session_id not in self.sessions:
            logger.warning(f"Session {session_id} not found")
            return False
        self.active_session_id = session_id
        logger.info(f"Active session: {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Lösche eine Session"""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        if self.active_session_id == session_id:
            self.active_session_id = None
        
        logger.info(f"Deleted session: {session_id}")
        return True
    
    # ============================================
    # MESSAGE MANAGEMENT
    # ============================================
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        session_id: Optional[str] = None,
    ) -> Optional[ConversationMessage]:
        """
        Füge eine Nachricht hinzu (zur aktiven oder spezifizierten Session)
        
        Args:
            role: "system", "user", oder "assistant"
            content: Der Nachrichtentext
            session_id: Wenn None, nutze active_session_id
            
        Returns:
            Die neue ConversationMessage oder None bei Fehler
            
        Raises:
            ValueError: Wenn no active session und session_id nicht angegeben
            
        Example:
            message = manager.add_message(
                MessageRole.USER,
                "Was ist dein Name?"
            )
        """
        target_session_id = session_id or self.active_session_id
        
        if not target_session_id:
            raise ValueError(
                "No active session. Create one first: "
                "manager.create_session() or set_active_session()"
            )
        
        session = self.get_session(target_session_id)
        if not session:
            raise ValueError(f"Session not found: {target_session_id}")
        
        # Füge Nachricht hinzu
        message = session.add_message(role, content)
        
        # Prüfe Context Limits
        self._enforce_context_limit(target_session_id)
        
        logger.debug(f"Added {role} message to session {target_session_id}")
        return message
    
    def get_messages(self, session_id: Optional[str] = None) -> List[ConversationMessage]:
        """Lade alle Nachrichten einer Session"""
        target_session_id = session_id or self.active_session_id
        
        if not target_session_id:
            return []
        
        session = self.get_session(target_session_id)
        return session.messages if session else []
    
    def get_conversation_history(
        self, session_id: Optional[str] = None
    ) -> List[dict]:
        """
        Hole Conversation History im LLM-Format
        
        Format:
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
            ]
        """
        target_session_id = session_id or self.active_session_id
        
        if not target_session_id:
            return []
        
        session = self.get_session(target_session_id)
        return session.get_messages_for_llm() if session else []
    
    def clear_session(self, session_id: Optional[str] = None) -> bool:
        """Lösche alle Nachrichten einer Session"""
        target_session_id = session_id or self.active_session_id
        
        if not target_session_id:
            return False
        
        session = self.get_session(target_session_id)
        if not session:
            return False
        
        session.messages.clear()
        logger.info(f"Cleared session: {target_session_id}")
        return True
    
    # ============================================
    # CONTEXT LIMIT MANAGEMENT
    # ============================================
    
    def _enforce_context_limit(self, session_id: str):
        """
        Prüfe und enforce Context Limits
        
        Strategie:
        1. Wenn über max_messages → entferne älteste Nachrichten (außer System)
        2. Wenn über max_tokens → entferne älteste Nachrichten
        3. Behalte immer preserve_first_n Nachrichten
        
        Später: Summarization wenn über threshold
        """
        session = self.get_session(session_id)
        if not session:
            return
        
        # Check Message Count
        if session.message_count() > self.config.max_messages:
            self._remove_oldest_messages(
                session_id,
                session.message_count() - self.config.max_messages
            )
        
        # Check Token Count
        if session.token_estimate() > self.config.max_tokens:
            self._remove_oldest_messages(session_id, 1)  # Remove 1 at a time
    
    def _remove_oldest_messages(self, session_id: str, count: int):
        """
        Entferne die ältesten Nachrichten (außer geschützten)
        
        Geschützte Nachrichten:
        - Erste preserve_first_n Nachrichten
        - System Messages (später: auch wenn wichtig)
        """
        session = self.get_session(session_id)
        if not session:
            return
        
        # Identifiziere geschützte Indizes
        protected_indices = set(range(self.config.preserve_first_n))
        
        # Entferne älteste nicht-geschützte Nachrichten
        removed = 0
        i = 0
        while i < len(session.messages) and removed < count:
            if i not in protected_indices:
                session.messages.pop(i)
                removed += 1
                logger.debug(
                    f"Removed message from session {session_id} "
                    f"(tokens/messages over limit)"
                )
            else:
                i += 1
    
    def get_context_stats(self, session_id: Optional[str] = None) -> dict:
        """Zeige Context-Nutzung"""
        target_session_id = session_id or self.active_session_id
        
        if not target_session_id:
            return {}
        
        session = self.get_session(target_session_id)
        if not session:
            return {}
        
        token_count = session.token_estimate()
        message_count = session.message_count()
        
        return {
            "session_id": target_session_id,
            "message_count": message_count,
            "max_messages": self.config.max_messages,
            "message_usage_pct": (message_count / self.config.max_messages) * 100,
            "token_count": token_count,
            "max_tokens": self.config.max_tokens,
            "token_usage_pct": (token_count / self.config.max_tokens) * 100,
            "at_limit": (
                message_count >= self.config.max_messages or
                token_count >= self.config.max_tokens
            ),
        }
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_stats(self) -> dict:
        """Zeige Statistiken über alle Sessions"""
        total_messages = sum(
            session.message_count()
            for session in self.sessions.values()
        )
        total_tokens = sum(
            session.token_estimate()
            for session in self.sessions.values()
        )
        
        return {
            "total_sessions": len(self.sessions),
            "active_session": self.active_session_id,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "config": {
                "max_tokens": self.config.max_tokens,
                "max_messages": self.config.max_messages,
                "preserve_first_n": self.config.preserve_first_n,
            },
        }


if __name__ == "__main__":
    # Quick test
    manager = ConversationManager()
    
    # Create session
    sid = manager.create_session("Test Conversation")
    manager.set_active_session(sid)
    
    # Add messages
    manager.add_message(MessageRole.SYSTEM, "Du bist hilfreich und freundlich")
    manager.add_message(MessageRole.USER, "Hallo!")
    manager.add_message(MessageRole.ASSISTANT, "Hallo! Wie kann ich dir helfen?")
    
    # Test conversation history
    history = manager.get_conversation_history()
    print("Conversation History:")
    for msg in history:
        print(f"  {msg['role']}: {msg['content'][:50]}...")
    
    # Test stats
    print("\nContext Stats:")
    print(manager.get_context_stats())
    
    print("\nManager Stats:")
    print(manager.get_stats())
