"""
api/routes/query.py — POST /query endpoint (fully wired).
"""
from fastapi import APIRouter, HTTPException
from api.schemas.query import QueryRequest, QueryResponse, SourceChunk

router = APIRouter()


@router.post("", response_model=QueryResponse, summary="Query the RAG pipeline")
async def query_rag(request: QueryRequest):
    """
    Retrieve relevant chunks via MMR and generate a grounded answer.
    Returns the answer plus source citations (page, type, preview).
    """
    try:
        from src.rag.pipeline import query_with_sources

        result = query_with_sources(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
        )

        sources = [
            SourceChunk(
                page=s["page"],
                content_type=s["content_type"],
                content_preview=s["content_preview"],
                score=s.get("score"),
            )
            for s in result["sources"]
        ]

        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=sources,
            llm_provider=result["llm_provider"],
            model=result["model"],
            retrieval_method=result["retrieval_method"],
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
