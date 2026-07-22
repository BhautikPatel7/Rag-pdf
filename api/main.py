"""
api/main.py — FastAPI application factory with lifespan & routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import ingest, query, evaluate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup: pre-load embedding model, warm up vector store
    print("[startup] RAG-PDF API is starting...")
    yield
    # Shutdown
    print("[shutdown] RAG-PDF API is stopping...")


app = FastAPI(
    title="RAG-PDF API",
    description=(
        "Multi-modal PDF Retrieval-Augmented Generation pipeline. "
        "Supports Text, Tables, Charts, Images, Emojis, Math, Logos and Icons."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ingest.router,   prefix="/ingest",   tags=["Ingest"])
app.include_router(query.router,    prefix="/query",    tags=["Query"])
app.include_router(evaluate.router, prefix="/evaluate", tags=["Evaluate"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return JSONResponse({"status": "ok", "service": "rag-pdf-api"})


@app.get("/", tags=["Health"])
async def root():
    return {"message": "RAG-PDF API — see /docs for endpoints."}
