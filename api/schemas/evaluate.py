"""
api/schemas/evaluate.py — Request/Response models for /evaluate endpoint.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class QAPair(BaseModel):
    question: str = Field(..., example="What is the faithfulness score of GPT-4o?")
    ground_truth: str = Field(..., example="GPT-4o achieved a faithfulness score of 0.93.")


class EvaluateRequest(BaseModel):
    qa_pairs: List[QAPair] = Field(
        ...,
        min_length=1,
        description="List of question + ground_truth pairs to evaluate against.",
    )
    collection_name: Optional[str] = Field(
        default=None,
        description="Vector store collection to query. Defaults to env CHROMA_COLLECTION_NAME.",
    )
    top_k: int = Field(default=5, ge=1, le=20)


class PerQuestionResult(BaseModel):
    question: str
    answer: str
    ground_truth: str
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
    context_recall: Optional[float] = None


class EvaluateResponse(BaseModel):
    # Aggregate scores
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float
    # Per-question breakdown
    details: List[PerQuestionResult]
    llm_provider: str
    num_questions: int
