"""
src/providers/llm_provider.py
Factory: returns the correct LangChain LLM based on LLM_PROVIDER env var.
Supports: "gemini" | "ollama"
"""
from functools import lru_cache
from langchain_core.language_models import BaseChatModel
from src.config.settings import get_settings


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """
    Return a LangChain chat model configured from settings.
    temperature=0.0 → deterministic answers (best for RAG).
    """
    settings = get_settings()

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=temperature,
        )

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}. Use 'gemini' or 'ollama'.")


def get_vision_llm() -> BaseChatModel:
    """
    Return a vision-capable LLM for image / chart / math description.
    Gemini 1.5 Flash has native vision. Ollama uses LLaVA.
    """
    settings = get_settings()

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,   # gemini-2.0-flash has native vision
            google_api_key=settings.gemini_api_key,
            temperature=0.0,
        )

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_vision_model,   # llava
            base_url=settings.ollama_base_url,
            temperature=0.0,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
