"""
api/schemas/ingest.py — Request/Response models for /ingest endpoint.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    pdf_path: str = Field(
        ...,
        description="Absolute path to the PDF file on the server (inside the container).",
        example="/data/pdfs/my_document.pdf",
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Custom vector store collection name. Defaults to env CHROMA_COLLECTION_NAME.",
    )


class ContentTypeSummary(BaseModel):
    text_chunks: int = 0
    table_chunks: int = 0
    image_chunks: int = 0
    math_chunks: int = 0
    emoji_chunks: int = 0


class IngestResponse(BaseModel):
    status: str
    pdf_path: str
    total_chunks: int
    content_summary: ContentTypeSummary
    vector_store: str
    collection: str
    llm_provider: str
    embedding_provider: str
    message: str
