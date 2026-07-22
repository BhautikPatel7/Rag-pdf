"""
src/providers/embedder_provider.py
Factory: returns the correct LangChain embedding model based on EMBEDDING_PROVIDER env var.
Supports: "local" (sentence-transformers) | "gemini"
"""
from functools import lru_cache
from langchain_core.embeddings import Embeddings
from src.config.settings import get_settings


@lru_cache(maxsize=1)
def get_embedder() -> Embeddings:
    """
    Return a LangChain embeddings object. Cached — model loads once at startup.
    """
    settings = get_settings()

    if settings.embedding_provider == "local":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=settings.local_embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    if settings.embedding_provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.gemini_api_key,
        )

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider!r}. Use 'local' or 'gemini'."
    )


def get_embedding_dimension() -> int:
    """Return the vector dimension for the current embedding model."""
    settings = get_settings()
    dims = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "BAAI/bge-large-en-v1.5": 1024,
    }
    if settings.embedding_provider == "local":
        return dims.get(settings.local_embedding_model, 384)
    if settings.embedding_provider == "gemini":
        return 768
    return 384
