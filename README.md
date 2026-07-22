# RAG-PDF — Multi-Modal PDF RAG Pipeline

Production-grade **Retrieval-Augmented Generation** pipeline for complex PDFs containing:
`Text` · `Tables` · `Charts` · `Images` · `Emojis` · `Math Equations` · `Logos` · `Icons`

---

## Quick Start with Docker

### 1. Clone & configure
```bash
git clone https://github.com/BhautikPatel7/Rag-pdf.git
cd Rag-pdf
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY or configure Ollama
```

### 2. Run (Gemini + ChromaDB — default)
```bash
docker compose up --build
```

### 3. Run with Ollama (fully local, no API keys)
```bash
# Edit .env: LLM_PROVIDER=ollama
docker compose --profile ollama up --build
```

### 4. API is live at
```
http://localhost:8000/docs   ← Swagger UI
http://localhost:8000/health ← Health check
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest` | Extract PDF content → embed → store in vector DB |
| `POST` | `/query` | Ask a question → MMR retrieval → LLM answer |
| `POST` | `/evaluate` | Run RAGAS evaluation on Q&A pairs |
| `GET` | `/health` | Health check |

### POST /ingest
```json
{ "pdf_path": "/data/pdfs/my_document.pdf" }
```

### POST /query
```json
{ "question": "What does the chart on page 3 show?", "top_k": 5 }
```

### POST /evaluate
```json
{
  "qa_pairs": [
    { "question": "What is X?", "ground_truth": "X is..." }
  ]
}
```

---

## Configuration (.env)

| Variable | Options | Default |
|---|---|---|
| `LLM_PROVIDER` | `gemini` \| `ollama` | `gemini` |
| `VECTOR_STORE` | `chromadb` \| `pinecone` | `chromadb` |
| `EMBEDDING_PROVIDER` | `local` \| `gemini` | `local` |
| `CHROMA_MODE` | `embedded` \| `server` | `embedded` |
| `CHUNK_SIZE` | integer | `1000` |

Full options: see [`.env.example`](.env.example)

---

## Project Structure

```
Rag-pdf/
├── api/                    ← FastAPI app
│   ├── main.py             ← App factory + lifespan
│   ├── routes/             ← ingest / query / evaluate
│   └── schemas/            ← Pydantic request/response models
├── src/
│   ├── config/settings.py  ← All config via pydantic-settings
│   ├── providers/          ← LLM / Embedder / VectorStore factories
│   ├── ingestion/          ← PDF extraction (text/table/image/math)
│   ├── vectorstore/        ← ChromaDB & Pinecone implementations
│   ├── rag/                ← Retrieval + LLM pipeline (LangChain LCEL)
│   └── evaluation/         ← RAGAS evaluation runner
├── tests/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── run.py                  ← Uvicorn entrypoint
```

---

## Docker Services

| Service | Image | Profile | Purpose |
|---|---|---|---|
| `rag-api` | local build | always | FastAPI RAG server |
| `chromadb` | `chromadb/chroma:0.5.4` | `chromadb` | Vector DB server mode |
| `ollama` | `ollama/ollama:latest` | `ollama` | Local LLM (LLaMA 3 + LLaVA) |

---

## Development

```bash
# Install deps locally
pip install -r requirements.txt

# Run with hot-reload (set API_RELOAD=true in .env)
python run.py

# Run tests
pytest tests/ -v
```
