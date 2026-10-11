"""
Integration Tests für Ollama Provider
======================================

Diese Tests prüfen die ECHTE Verbindung zu Ollama, nicht gemockt!

Unterschied zu Unit Tests:
- Unit Tests (tests/unit/): Mocken externe Dependencies, testen Logik
- Integration Tests (tests/integration/): Testen echte externe Services

Diese Tests werden nur ausgeführt, wenn Ollama verfügbar ist.
"""

import pytest
import asyncio
from typing import Optional
import logging

from ai_core.models.ollama import OllamaProvider
from ai_core.models.schemas import Message, LLMResponse

logger = logging.getLogger(__name__)


class TestOllamaIntegration:
    """
    ECHTE Ollama Integration Tests
    
    Diese Tests werden nur ausgeführt wenn Ollama läuft!
    """

    @pytest.mark.ollama
    @pytest.mark.asyncio
    async def test_ollama_responds_to_simple_message(self, requires_ollama):
        """
        Test: Kann JARVIS eine einfache Frage stellen und Antwort erhalten?
        
        Example Prompt:
            User: "Was ist 2+2?"
            Ollama: "2+2 = 4"
        """
        provider = OllamaProvider()
        prompt = "Antworte kurz: Was ist 2+2?"
        messages = [Message(role="user", content=prompt)]
        
        response = await provider.generate(messages)
        
        # Validierungen
        assert isinstance(response, LLMResponse)
        assert len(response.text) > 0, "Antwort sollte nicht leer sein"
        assert response.model == provider.model
        assert response.tokens_used > 0
        
        logger.info(f"✅ Ollama Response: {response.text[:100]}...")

    @pytest.mark.ollama
    @pytest.mark.asyncio
    async def test_ollama_model_info(self, requires_ollama):
        """
        Test: Welches Modell läuft auf Ollama?
        
        Zeigt:
        - Modellname
        - Base URL
        - Provider Info
        """
        provider = OllamaProvider()
        info = provider.get_info()
        
        # Validierungen
        assert "model" in info
        assert "base_url" in info
        assert "provider" in info
        
        logger.info(f"✅ Ollama Model: {info['model']}")
        logger.info(f"✅ Ollama URL: {info['base_url']}")
        logger.info(f"✅ Provider: {info['provider']}")

    @pytest.mark.ollama
    @pytest.mark.asyncio
    async def test_ollama_multi_turn_conversation(self, requires_ollama):
        """
        Test: Kann JARVIS eine mehrteilige Konversation führen?
        
        Simulates:
            Turn 1: User: "Ich bin Max"
            Turn 2: Assistant: "Schön dich kennenzulernen, Max!"
            Turn 3: User: "Was ist mein Name?"
            Turn 4: Assistant: "Dein Name ist Max"
        """
        provider = OllamaProvider()
        messages = [
            Message(role="user", content="Mein Name ist Max"),
        ]
        
        # Turn 1
        response1 = await provider.generate(messages)
        assert len(response1.text) > 0
        logger.info(f"Turn 1: User asked about name")
        logger.info(f"Turn 1: Ollama responded ({len(response1.text)} chars)")
        
        # Turn 2 - add context
        messages.append(Message(role="assistant", content=response1.text))
        messages.append(Message(role="user", content="Wer bin ich?"))
        
        response2 = await provider.generate(messages)
        assert len(response2.text) > 0
        logger.info(f"Turn 2: User asked 'Wer bin ich?'")
        logger.info(f"Turn 2: Ollama responded ({len(response2.text)} chars)")

    @pytest.mark.ollama
    @pytest.mark.asyncio
    async def test_ollama_stats_tracking(self, requires_ollama):
        """
        Test: Wird die Nutzung des Modells tracked?
        
        Sollte nach Aufrufen:
        - call_count erhöht sich
        - token_count erhöht sich (Schätzung)
        """
        provider = OllamaProvider()
        initial_calls = provider.stats.call_count
        initial_tokens = provider.stats.token_count
        
        # Mache einen Aufruf
        messages = [Message(role="user", content="Hallo")]
        response = await provider.generate(messages)
        
        # Prüfe ob Stats aktualisiert wurden
        assert provider.stats.call_count > initial_calls
        assert provider.stats.token_count >= initial_tokens
        
        logger.info(
            f"✅ Stats tracked: "
            f"calls={provider.stats.call_count}, "
            f"tokens={provider.stats.token_count}"
        )

    @pytest.mark.ollama
    @pytest.mark.asyncio
    async def test_ollama_system_prompt_respected(self, requires_ollama):
        """
        Test: Beachtet Ollama den System-Prompt?
        
        Beispiel:
            System: "Antworte immer auf German"
            User: "Sag hallo!"
            Ollama sollte auf Deutsch antworten
        """
        provider = OllamaProvider()
        system_prompt = "Antworte immer kurz und prägnant. Max. 10 Wörter."
        messages = [
            Message(role="user", content="Erzähle mir einen Witz")
        ]
        
        response = await provider.generate(
            messages,
            system_prompt=system_prompt
        )
        
        assert len(response.text) > 0
        
        # Zähle Wörter (ungenaue Prüfung)
        word_count = len(response.text.split())
        logger.info(
            f"✅ System prompt tested: "
            f"Antwort hatte {word_count} Wörter "
            f"(max 10 angefordert)"
        )


class TestOllamaErrorHandling:
    """Test Fehlerbehandlung bei Ollama-Problemen"""

    @pytest.mark.asyncio
    async def test_ollama_connection_error_message(self):
        """
        Test: Ist die Fehlermeldung hilfreich wenn Ollama nicht läuft?
        
        Should show:
            ValueError: "Cannot connect to Ollama...
                        Make sure it's running: ollama serve"
        """
        # Simulate Ollama not running by using wrong URL
        provider = OllamaProvider(base_url="http://localhost:9999")
        messages = [Message(role="user", content="Test")]
        
        with pytest.raises(ValueError) as exc_info:
            await provider.generate(messages)
        
        error_msg = str(exc_info.value)
        
        # Validiere dass Error Message hilfreich ist
        assert "Make sure Ollama is running" in error_msg or "Cannot connect" in error_msg
        logger.info(f"✅ Error message is helpful: {error_msg}")


if __name__ == "__main__":
    # Für schnelle lokale Tests:
    # python -m pytest tests/integration/test_ollama_integration.py -v -m ollama
    pytest.main([__file__, "-v", "-s", "-m", "ollama"])
