"""
api/schemas/query.py — Request/Response models for /query endpoint.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        description="The question to answer from the PDF content.",
        example="What does the revenue chart on page 3 show?",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve.")
    collection_name: Optional[str] = Field(
        default=None,
        description="Vector store collection to query. Defaults to env CHROMA_COLLECTION_NAME.",
    )


class SourceChunk(BaseModel):
    page: int
    content_type: str   # "text" | "table" | "image" | "math" | "emoji"
    content_preview: str
    score: Optional[float] = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceChunk]
    llm_provider: str
    model: str
    retrieval_method: str
