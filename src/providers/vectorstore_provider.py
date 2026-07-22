"""
src/providers/vectorstore_provider.py
Factory: returns the correct VectorStore implementation based on VECTOR_STORE env var.
Supports: "chromadb" | "pinecone"
"""
from typing import Optional
from src.vectorstore.base import AbstractVectorStore
from src.config.settings import get_settings


def get_vectorstore(collection_name: Optional[str] = None) -> AbstractVectorStore:
    """
    Return a VectorStore implementation based on VECTOR_STORE setting.
    collection_name overrides the default from settings.
    """
    settings = get_settings()

    if settings.vector_store == "chromadb":
        from src.vectorstore.chroma_store import ChromaVectorStore
        return ChromaVectorStore(collection_name=collection_name)

    if settings.vector_store == "pinecone":
        from src.vectorstore.pinecone_store import PineconeStore
        return PineconeStore(collection_name=collection_name)

    raise ValueError(
        f"Unknown VECTOR_STORE: {settings.vector_store!r}. Use 'chromadb' or 'pinecone'."
    )
