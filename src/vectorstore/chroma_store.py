"""
src/vectorstore/chroma_store.py
ChromaDB implementation of AbstractVectorStore.
Supports two modes:
  - "embedded" : ChromaDB runs in-process (no extra container)
  - "server"   : connects to chromadb service in docker-compose
"""
import os
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma

from src.vectorstore.base import AbstractVectorStore
from src.providers.embedder_provider import get_embedder
from src.config.settings import get_settings


class ChromaVectorStore(AbstractVectorStore):

    def __init__(self, collection_name: Optional[str] = None):
        settings = get_settings()
        self._collection_name = collection_name or settings.chroma_collection_name
        self._embedder = get_embedder()
        self._store = self._init_store(settings)

    def _init_store(self, settings) -> Chroma:
        if settings.chroma_mode == "server":
            import chromadb
            client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
            return Chroma(
                client=client,
                collection_name=self._collection_name,
                embedding_function=self._embedder,
            )
        else:
            # Embedded mode — ChromaDB stores files in chroma_persist_dir
            os.makedirs(settings.chroma_persist_dir, exist_ok=True)
            return Chroma(
                collection_name=self._collection_name,
                embedding_function=self._embedder,
                persist_directory=settings.chroma_persist_dir,
            )

    # ── Interface implementation ───────────────────────────────────────────────

    def add_documents(self, documents: List[Document]) -> int:
        if not documents:
            return 0
        self._store.add_documents(documents)
        return len(documents)

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        return self._store.similarity_search(query, k=k, filter=filter)

    def as_retriever(self, search_type: str = "mmr", k: int = 5):
        search_kwargs: dict = {"k": k}
        if search_type == "mmr":
            search_kwargs["fetch_k"] = k * 3   # fetch more, then diversify
            search_kwargs["lambda_mult"] = 0.6  # 0=max diversity, 1=max relevance
        return self._store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def delete_collection(self) -> None:
        self._store.delete_collection()

    def collection_exists(self) -> bool:
        return self.document_count() > 0

    def document_count(self) -> int:
        try:
            return self._store._collection.count()
        except Exception:
            return 0
