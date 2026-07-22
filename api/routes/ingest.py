"""
api/routes/ingest.py — POST /ingest endpoint (fully wired).
"""
from fastapi import APIRouter, HTTPException
from api.schemas.ingest import IngestRequest, IngestResponse, ContentTypeSummary
from src.config.settings import get_settings

router = APIRouter()


@router.post("", response_model=IngestResponse, summary="Ingest a PDF into the vector store")
async def ingest_pdf(request: IngestRequest):
    """
    Extract all content types from the PDF at `pdf_path` and store
    embeddings in the configured vector store (ChromaDB or Pinecone).

    Handles: Text · Tables · Images · Charts · Math · Emojis · Logos · Icons
    """
    settings = get_settings()

    try:
        from src.ingestion.pdf_extractor import extract_pdf
        from src.providers.vectorstore_provider import get_vectorstore

        # 1. Extract all content from PDF
        print(f"[ingest] Starting extraction: {request.pdf_path}")
        documents, summary = extract_pdf(request.pdf_path)

        if not documents:
            raise HTTPException(
                status_code=422,
                detail="No content could be extracted from the PDF."
            )

        # 2. Store in vector store
        store = get_vectorstore(collection_name=request.collection_name)
        stored = store.add_documents(documents)
        print(f"[ingest] Stored {stored} chunks in {settings.vector_store}")

        collection = request.collection_name or settings.chroma_collection_name

        return IngestResponse(
            status="success",
            pdf_path=request.pdf_path,
            total_chunks=summary.total_chunks,
            content_summary=ContentTypeSummary(
                text_chunks=summary.text_chunks,
                table_chunks=summary.table_chunks,
                image_chunks=summary.image_chunks,
                math_chunks=summary.math_chunks,
                emoji_chunks=summary.emoji_chunks,
            ),
            vector_store=settings.vector_store,
            collection=collection,
            llm_provider=settings.llm_provider,
            embedding_provider=settings.embedding_provider,
            message=f"Successfully ingested {summary.total_chunks} chunks from {summary.total_pages} pages.",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
