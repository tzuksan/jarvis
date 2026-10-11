"""
Unit Tests für Conversation Manager
====================================

Test Coverage:
- Message Management (add, retrieve, clear)
- Session Management (create, load, delete, list)
- Context Limits (token & message count)
- Multiple Sessions
- Conversation History für LLM
"""

import pytest
from datetime import datetime

from ai_core.conversation import (
    ConversationManager,
    ConversationSession,
    ConversationMessage,
    MessageRole,
    ConversationContextConfig,
    InMemoryConversationStorage,
)


class TestConversationMessage:
    """Test ConversationMessage Model"""
    
    def test_message_creation(self):
        """Erstelle eine Nachricht"""
        msg = ConversationMessage(
            role=MessageRole.USER,
            content="Hallo!"
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hallo!"
        assert isinstance(msg.timestamp, datetime)
    
    def test_message_with_metadata(self):
        """Nachricht mit Metadata"""
        meta = {"confidence": 0.95}
        msg = ConversationMessage(
            role=MessageRole.ASSISTANT,
            content="Antwort",
            metadata=meta
        )
        
        assert msg.metadata == meta


class TestConversationSession:
    """Test ConversationSession Model"""
    
    def test_session_creation(self):
        """Erstelle eine Session"""
        session = ConversationSession(
            session_id="test-1",
            title="Test Session"
        )
        
        assert session.session_id == "test-1"
        assert session.title == "Test Session"
        assert session.message_count() == 0
    
    def test_add_message(self):
        """Füge Nachricht zu Session hinzu"""
        session = ConversationSession(session_id="test-1")
        
        session.add_message(MessageRole.USER, "Hallo")
        
        assert session.message_count() == 1
        assert session.messages[0].content == "Hallo"
        assert session.messages[0].role == MessageRole.USER
    
    def test_get_messages_for_llm(self):
        """Konvertiere zu LLM Format"""
        session = ConversationSession(session_id="test-1")
        session.add_message(MessageRole.SYSTEM, "Du bist hilfreich")
        session.add_message(MessageRole.USER, "Hallo!")
        session.add_message(MessageRole.ASSISTANT, "Hallo zurück!")
        
        llm_format = session.get_messages_for_llm()
        
        assert len(llm_format) == 3
        assert llm_format[0]["role"] == "system"
        assert llm_format[1]["role"] == "user"
        assert llm_format[2]["role"] == "assistant"
    
    def test_token_estimate(self):
        """Schätze Token Count"""
        session = ConversationSession(session_id="test-1")
        session.add_message(MessageRole.USER, "x" * 400)  # ~100 tokens
        
        tokens = session.token_estimate()
        
        # 400 chars / 4 = 100 tokens
        assert tokens == 100


class TestConversationManager:
    """Test ConversationManager"""
    
    def test_manager_initialization(self):
        """Initialisiere Manager"""
        manager = ConversationManager()
        
        assert manager.config.max_tokens == 4000
        assert manager.config.max_messages == 50
        assert manager.active_session_id is None
    
    def test_create_session(self):
        """Erstelle neue Session"""
        manager = ConversationManager()
        
        session_id = manager.create_session("Test Session")
        
        assert session_id is not None
        assert len(session_id) > 0
        assert manager.get_session(session_id) is not None
    
    def test_set_active_session(self):
        """Setze aktive Session"""
        manager = ConversationManager()
        sid = manager.create_session()
        
        success = manager.set_active_session(sid)
        
        assert success
        assert manager.active_session_id == sid
    
    def test_delete_session(self):
        """Lösche Session"""
        manager = ConversationManager()
        sid = manager.create_session()
        
        manager.delete_session(sid)
        
        assert manager.get_session(sid) is None
    
    def test_add_message_to_active_session(self):
        """Füge Nachricht zur aktiven Session hinzu"""
        manager = ConversationManager()
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        message = manager.add_message(MessageRole.USER, "Hallo!")
        
        assert message is not None
        assert message.content == "Hallo!"
        assert message.role == MessageRole.USER
    
    def test_add_message_to_specific_session(self):
        """Füge Nachricht zu spezifischer Session hinzu"""
        manager = ConversationManager()
        sid1 = manager.create_session("Session 1")
        sid2 = manager.create_session("Session 2")
        manager.set_active_session(sid1)
        
        # Füge zu Session 2 hinzu (nicht aktiv)
        manager.add_message(MessageRole.USER, "Nachricht für S2", session_id=sid2)
        
        # Prüfe dass in S2
        messages_s2 = manager.get_messages(sid2)
        assert len(messages_s2) == 1
        
        # Prüfe dass nicht in S1
        messages_s1 = manager.get_messages(sid1)
        assert len(messages_s1) == 0
    
    def test_add_message_error_no_session(self):
        """Error wenn keine aktive Session"""
        manager = ConversationManager()
        
        with pytest.raises(ValueError):
            manager.add_message(MessageRole.USER, "Hallo")
    
    def test_get_conversation_history(self):
        """Hole Conversation History im LLM Format"""
        manager = ConversationManager()
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        manager.add_message(MessageRole.SYSTEM, "Du bist hilfreich")
        manager.add_message(MessageRole.USER, "Was ist 2+2?")
        manager.add_message(MessageRole.ASSISTANT, "2+2 = 4")
        
        history = manager.get_conversation_history()
        
        assert len(history) == 3
        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"
    
    def test_clear_session(self):
        """Lösche alle Nachrichten einer Session"""
        manager = ConversationManager()
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        manager.add_message(MessageRole.USER, "Message 1")
        manager.add_message(MessageRole.USER, "Message 2")
        
        assert len(manager.get_messages()) == 2
        
        manager.clear_session()
        
        assert len(manager.get_messages()) == 0
    
    def test_list_sessions(self):
        """Liste Sessions auf"""
        manager = ConversationManager()
        manager.create_session("Session 1")
        manager.create_session("Session 2")
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 2
        assert all("session_id" in s for s in sessions)
        assert all("title" in s for s in sessions)


class TestContextLimits:
    """Test Context Limit Enforcement"""
    
    def test_message_count_limit(self):
        """Prüfe dass alte Nachrichten entfernt werden"""
        config = ConversationContextConfig(
            max_messages=3,
            preserve_first_n=1  # Behalte erste Nachricht
        )
        manager = ConversationManager(config)
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        # Füge 5 Nachrichten hinzu
        manager.add_message(MessageRole.SYSTEM, "System")
        manager.add_message(MessageRole.USER, "Msg 1")
        manager.add_message(MessageRole.USER, "Msg 2")
        manager.add_message(MessageRole.USER, "Msg 3")
        manager.add_message(MessageRole.USER, "Msg 4")
        
        # Sollte nur 3 haben (preserve_first_n + 2 others)
        messages = manager.get_messages()
        assert len(messages) <= 3
        
        # Erste sollte noch da sein
        assert messages[0].content == "System"
    
    def test_token_count_limit(self):
        """Prüfe dass zu viele Tokens entfernt werden"""
        config = ConversationContextConfig(
            max_tokens=100,  # Klein!
            preserve_first_n=1
        )
        manager = ConversationManager(config)
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        # Füge große Nachrichten hinzu
        manager.add_message(MessageRole.SYSTEM, "x" * 20)
        manager.add_message(MessageRole.USER, "x" * 400)
        manager.add_message(MessageRole.USER, "x" * 400)
        
        # Token sollte über limit gehen und alte Nachrichten entfernen
        session = manager.get_session(sid)
        tokens = session.token_estimate()
        
        # Sollte unter max_tokens sein
        assert tokens <= config.max_tokens
    
    def test_context_stats(self):
        """Zeige Context Stats"""
        manager = ConversationManager()
        sid = manager.create_session()
        manager.set_active_session(sid)
        
        manager.add_message(MessageRole.USER, "Hello")
        
        stats = manager.get_context_stats()
        
        assert stats["message_count"] == 1
        assert stats["max_messages"] == 50
        assert "message_usage_pct" in stats
        assert "token_count" in stats
        assert "at_limit" in stats


class TestMultipleSessions:
    """Test mehrere parallele Sessions"""
    
    def test_multiple_independent_sessions(self):
        """Teste dass Sessions unabhängig sind"""
        manager = ConversationManager()
        sid1 = manager.create_session("Session 1")
        sid2 = manager.create_session("Session 2")
        
        manager.set_active_session(sid1)
        manager.add_message(MessageRole.USER, "S1 Message")
        
        manager.set_active_session(sid2)
        manager.add_message(MessageRole.USER, "S2 Message")
        
        # Prüfe dass getrennt
        messages_s1 = manager.get_messages(sid1)
        messages_s2 = manager.get_messages(sid2)
        
        assert len(messages_s1) == 1
        assert len(messages_s2) == 1
        assert messages_s1[0].content == "S1 Message"
        assert messages_s2[0].content == "S2 Message"
    
    def test_session_isolation(self):
        """Prüfe dass Clear nur aktive Session löscht"""
        manager = ConversationManager()
        sid1 = manager.create_session()
        sid2 = manager.create_session()
        
        manager.set_active_session(sid1)
        manager.add_message(MessageRole.USER, "S1 Msg")
        
        manager.set_active_session(sid2)
        manager.add_message(MessageRole.USER, "S2 Msg")
        manager.clear_session()  # Clear S2
        
        # S1 sollte noch Nachricht haben
        messages_s1 = manager.get_messages(sid1)
        messages_s2 = manager.get_messages(sid2)
        
        assert len(messages_s1) == 1
        assert len(messages_s2) == 0


class TestStatistics:
    """Test Manager Statistics"""
    
    def test_get_stats(self):
        """Hole Manager Stats"""
        manager = ConversationManager()
        sid1 = manager.create_session("S1")
        sid2 = manager.create_session("S2")
        
        manager.set_active_session(sid1)
        manager.add_message(MessageRole.USER, "Message 1")
        
        manager.set_active_session(sid2)
        manager.add_message(MessageRole.USER, "Message 2")
        manager.add_message(MessageRole.USER, "Message 3")
        
        stats = manager.get_stats()
        
        assert stats["total_sessions"] == 2
        assert stats["total_messages"] == 3
        assert stats["active_session"] == sid2


class TestStorageInterface:
    """Test Storage Interface"""
    
    @pytest.mark.asyncio
    async def test_in_memory_storage(self):
        """Teste InMemoryConversationStorage"""
        storage = InMemoryConversationStorage()
        
        session = ConversationSession(session_id="test-1")
        session.add_message(MessageRole.USER, "Hello")
        
        # Save
        success = await storage.save_session(session)
        assert success
        
        # Load
        loaded = await storage.load_session("test-1")
        assert loaded is not None
        assert loaded.message_count() == 1
        
        # List
        sessions = await storage.list_sessions()
        assert len(sessions) == 1
        
        # Delete
        success = await storage.delete_session("test-1")
        assert success
        
        loaded = await storage.load_session("test-1")
        assert loaded is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
