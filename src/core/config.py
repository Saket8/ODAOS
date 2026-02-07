"""ODAOS Core Configuration Module.

Provides environment-based configuration with support for multiple LLM providers
(Groq, Ollama, Anthropic) enabling seamless provider switching without code changes.
"""
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class Settings(BaseSettings):
    """ODAOS Application Settings.
    
    Configuration is loaded from environment variables and .env file.
    Provider switching is controlled by ODAOS_LLM_PROVIDER environment variable.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # LLM Provider Settings
    odaos_llm_provider: LLMProvider = Field(
        default=LLMProvider.GROQ,
        description="Active LLM provider (groq, ollama, anthropic)"
    )
    
    # Groq Settings
    groq_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Groq API key for cloud LLM access"
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model name"
    )
    
    # Gemini Settings
    google_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Google AI Studio API key for Gemini"
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model name"
    )
    
    # OpenRouter Settings
    openrouter_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenRouter API key"
    )
    openrouter_model: str = Field(
        default="deepseek/deepseek-chat",
        description="OpenRouter model name"
    )
    
    # Ollama Settings (for local development)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL"
    )
    ollama_model: str = Field(
        default="qwen3-coder",
        description="Ollama model name"
    )
    
    # Anthropic Settings (for production)
    anthropic_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Anthropic API key"
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Anthropic model name"
    )
    
    # OCI Settings
    oci_config_path: Path = Field(
        default=Path.home() / ".oci" / "config",
        description="Path to OCI config file"
    )
    oci_profile: str = Field(
        default="DEFAULT",
        description="OCI config profile name"
    )
    
    # Oracle Database Settings
    oracle_dsn: Optional[str] = Field(
        default=None,
        description="Oracle connection string (host:port/service)"
    )
    oracle_user: Optional[str] = Field(
        default=None,
        description="Oracle database username"
    )
    oracle_password: Optional[SecretStr] = Field(
        default=None,
        description="Oracle database password"
    )
    oracle_client_path: Optional[str] = Field(
        default=None,
        description="Path to Oracle Instant Client for thick mode (required for NNE)"
    )
    
    # SSH Tunnel Settings (for MVP via Bastion)
    bastion_host: Optional[str] = Field(
        default=None,
        description="Public IP of OCI Bastion host"
    )
    bastion_user: str = Field(
        default="opc",
        description="SSH user for Bastion access"
    )
    bastion_key_path: Optional[str] = Field(
        default=None,
        description="Path to SSH private key for Bastion"
    )
    db_private_ip: Optional[str] = Field(
        default=None,
        description="Private IP of database server"
    )
    db_port: int = Field(
        default=1521,
        description="Database port"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    def get_active_model(self) -> str:
        """Get the model name for the active provider."""
        if self.odaos_llm_provider == LLMProvider.GROQ:
            return self.groq_model
        elif self.odaos_llm_provider == LLMProvider.OLLAMA:
            return self.ollama_model
        elif self.odaos_llm_provider == LLMProvider.ANTHROPIC:
            return self.anthropic_model
        elif self.odaos_llm_provider == LLMProvider.GEMINI:
            return self.gemini_model
        elif self.odaos_llm_provider == LLMProvider.OPENROUTER:
            return self.openrouter_model
        raise ValueError(f"Unknown provider: {self.odaos_llm_provider}")


# Global settings instance (lazy loaded)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
