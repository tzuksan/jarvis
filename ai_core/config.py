"""Configuration management for JARVIS AI Core"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # LLM Configuration (Provider-agnostic)
    llm_provider: str = "ollama"  # Options: "ollama", "openai", "anthropic"
    
    # Ollama Configuration (Local, Primary)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"  # or "neural-chat", "dolphin-mixtral", etc.
    
    # OpenAI Configuration (Cloud fallback)
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openai_vision_model: str = "gpt-4-vision-preview"
    
    # Anthropic Configuration (Cloud fallback - future)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Common LLM Parameters
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout_seconds: int = 60
    
    # Database
    database_url: str = "sqlite:///./jarvis_data.db"
    
    # PC Agent
    pc_agent_host: str = "0.0.0.0"
    pc_agent_port: int = 8000
    pc_agent_workers: int = 4
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/jarvis.log"
    debug: bool = False
    environment: str = "development"
    
    # Security
    allow_tool_confirmation: bool = True
    tool_execution_timeout: int = 30
    
    # Conversation
    max_conversation_history: int = 50
    cache_ttl_seconds: int = 300
    
    # Voice
    whisper_api_key: str = ""
    whisper_model: str = "whisper-1"
    tts_provider: str = "edge_tts"
    voice_sample_rate: int = 16000
    voice_channels: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

