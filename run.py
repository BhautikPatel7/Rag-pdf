"""
run.py — Uvicorn entrypoint for the RAG-PDF FastAPI server.
"""
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info"),
        workers=1,  # keep at 1 for in-process ChromaDB
    )
