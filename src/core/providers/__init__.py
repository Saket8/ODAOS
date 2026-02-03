"""LangChain-based LLM Provider Factory.

Provides a unified interface for creating LLM instances across different providers
(Groq, Ollama, Anthropic) using LangChain's ChatModel abstraction.

Usage:
    from src.core.providers import create_llm
    
    # Uses provider from environment (ODAOS_LLM_PROVIDER)
    llm = create_llm()
    
    # Or override provider
    llm = create_llm(provider="groq")
"""
from typing import Optional

from langchain_core.language_models import BaseChatModel

from ..config import get_settings, LLMProvider


def create_llm(
    provider: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    **kwargs
) -> BaseChatModel:
    """Create a LangChain ChatModel for the specified provider.
    
    Args:
        provider: LLM provider name (groq, ollama, anthropic). 
                  If None, uses ODAOS_LLM_PROVIDER from environment.
        temperature: Model temperature for response variability.
        max_tokens: Maximum tokens in response.
        **kwargs: Additional provider-specific arguments.
    
    Returns:
        LangChain BaseChatModel instance.
    
    Raises:
        ValueError: If provider is unknown or API key is missing.
    """
    settings = get_settings()
    
    # Determine provider
    if provider:
        active_provider = LLMProvider(provider.lower())
    else:
        active_provider = settings.odaos_llm_provider
    
    if active_provider == LLMProvider.GROQ:
        return _create_groq_llm(settings, temperature, max_tokens, **kwargs)
    elif active_provider == LLMProvider.OLLAMA:
        return _create_ollama_llm(settings, temperature, max_tokens, **kwargs)
    elif active_provider == LLMProvider.ANTHROPIC:
        return _create_anthropic_llm(settings, temperature, max_tokens, **kwargs)
    elif active_provider == LLMProvider.GEMINI:
        return _create_gemini_llm(settings, temperature, max_tokens, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {active_provider}")


def _create_groq_llm(settings, temperature: float, max_tokens: int, **kwargs) -> BaseChatModel:
    """Create Groq LLM instance using langchain-groq."""
    from langchain_groq import ChatGroq
    
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable is required for Groq provider")
    
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key.get_secret_value(),
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def _create_ollama_llm(settings, temperature: float, max_tokens: int, **kwargs) -> BaseChatModel:
    """Create Ollama LLM instance for local models."""
    from langchain_community.chat_models import ChatOllama
    
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
        num_predict=max_tokens,
        **kwargs
    )


def _create_anthropic_llm(settings, temperature: float, max_tokens: int, **kwargs) -> BaseChatModel:
    """Create Anthropic LLM instance for Claude models."""
    from langchain_anthropic import ChatAnthropic
    
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
    
    return ChatAnthropic(
        model=settings.anthropic_model,
        api_key=settings.anthropic_api_key.get_secret_value(),
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )


def _create_gemini_llm(settings, temperature: float, max_tokens: int, **kwargs) -> BaseChatModel:
    """Create Google Gemini LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini provider")
    
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key.get_secret_value(),
        temperature=temperature,
        max_output_tokens=max_tokens,
        **kwargs
    )


def get_provider_info() -> dict:
    """Get information about the currently configured provider.
    
    Returns:
        Dictionary with provider name, model, and status.
    """
    settings = get_settings()
    
    provider = settings.odaos_llm_provider.value
    model = settings.get_active_model()
    
    # Check if credentials are available
    if provider == "groq":
        has_credentials = bool(settings.groq_api_key)
    elif provider == "ollama":
        has_credentials = True  # Local, no credentials needed
    elif provider == "anthropic":
        has_credentials = bool(settings.anthropic_api_key)
    elif provider == "gemini":
        has_credentials = bool(settings.google_api_key)
    else:
        has_credentials = False
    
    return {
        "provider": provider,
        "model": model,
        "has_credentials": has_credentials,
        "ready": has_credentials,
    }
