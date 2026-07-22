"""
src/vectorstore/pinecone_store.py
Pinecone implementation of AbstractVectorStore.
Uses the pinecone>=3.0.0 SDK (package name: pinecone, not pinecone-client).
"""
from typing import List, Optional

from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore

from src.vectorstore.base import AbstractVectorStore
from src.providers.embedder_provider import get_embedder, get_embedding_dimension
from src.config.settings import get_settings


class PineconeStore(AbstractVectorStore):

    def __init__(self, collection_name: Optional[str] = None):
        settings = get_settings()
        self._index_name = collection_name or settings.pinecone_index_name
        self._embedder = get_embedder()
        self._store = self._init_store(settings)

    def _init_store(self, settings) -> PineconeVectorStore:
        from pinecone import Pinecone, ServerlessSpec

        pc = Pinecone(api_key=settings.pinecone_api_key)

        # Create index if it doesn't exist
        existing = [i.name for i in pc.list_indexes()]
        if self._index_name not in existing:
            dim = get_embedding_dimension()
            pc.create_index(
                name=self._index_name,
                dimension=dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.pinecone_environment,
                ),
            )

        index = pc.Index(self._index_name)
        return PineconeVectorStore(index=index, embedding=self._embedder)

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
            search_kwargs["fetch_k"] = k * 3
            search_kwargs["lambda_mult"] = 0.6
        return self._store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs,
        )

    def delete_collection(self) -> None:
        from pinecone import Pinecone
        settings = get_settings()
        pc = Pinecone(api_key=settings.pinecone_api_key)
        pc.delete_index(self._index_name)

    def collection_exists(self) -> bool:
        return self.document_count() > 0

    def document_count(self) -> int:
        try:
            stats = self._store._index.describe_index_stats()
            return stats.get("total_vector_count", 0)
        except Exception:
            return 0
