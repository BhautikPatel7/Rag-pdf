"""
src/config/settings.py
Reads all configuration from environment / .env file via pydantic-settings.
All other modules import `get_settings()` — never read os.environ directly.
"""
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── API ────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    log_level: str = "info"

    # ── LLM Provider ──────────────────────────────────────────
    llm_provider: Literal["gemini", "ollama"] = "gemini"

    # Gemini
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.5-flash"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_vision_model: str = "llava"

    # ── Embedding ─────────────────────────────────────────────
    embedding_provider: Literal["local", "gemini"] = "local"
    local_embedding_model: str = "all-MiniLM-L6-v2"

    # ── Vector Store ──────────────────────────────────────────
    vector_store: Literal["chromadb", "pinecone"] = "chromadb"

    # ChromaDB
    chroma_mode: Literal["embedded", "server"] = "embedded"
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "rag_pdf_collection"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000

    # Pinecone
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "rag-pdf"
    pinecone_environment: str = "us-east-1"
    pinecone_dimension: int = 384

    # ── Ingestion ─────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    pdf_upload_dir: str = "/data/pdfs"

    # ── RAGAS ─────────────────────────────────────────────────
    ragas_faithfulness: bool = True
    ragas_answer_relevancy: bool = True
    ragas_context_precision: bool = True
    ragas_context_recall: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
