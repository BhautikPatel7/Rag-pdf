"""
src/vectorstore/base.py
Abstract interface that both ChromaDB and Pinecone implementations must satisfy.
Routes only call this interface — never touch a specific store directly.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from langchain_core.documents import Document


class AbstractVectorStore(ABC):

    @abstractmethod
    def add_documents(self, documents: List[Document]) -> int:
        """
        Embed and store a list of LangChain Documents.
        Returns the number of chunks successfully stored.
        """

    @abstractmethod
    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        """Return top-k most similar documents for the query string."""

    @abstractmethod
    def as_retriever(self, search_type: str = "mmr", k: int = 5):
        """Return a LangChain retriever (for use in LCEL chains)."""

    @abstractmethod
    def delete_collection(self) -> None:
        """Drop the entire collection / index."""

    @abstractmethod
    def collection_exists(self) -> bool:
        """Return True if the collection/index has any documents."""

    @abstractmethod
    def document_count(self) -> int:
        """Return number of vectors stored."""
