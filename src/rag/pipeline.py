"""
src/rag/pipeline.py
End-to-end RAG pipeline using LangChain LCEL (LangChain Expression Language).

Pipeline: question → retriever → format_docs → prompt → LLM → answer

Also exposes query_with_sources() which returns both the answer and
the source chunks used to generate it.
"""
from typing import Optional
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.rag.prompt import get_rag_prompt, format_docs
from src.providers.llm_provider import get_llm
from src.providers.vectorstore_provider import get_vectorstore


def build_rag_chain(collection_name: Optional[str] = None, top_k: int = 5):
    """
    Build and return the LCEL RAG chain.

    Chain flow:
      question (str)
         │
         ├──► retriever (MMR, top-k) → List[Document]
         │         │
         │         └──► format_docs() → context str
         │
         ├──► RunnablePassthrough (keeps question for prompt)
         │
         ▼
      prompt (system + human)
         │
         ▼
      LLM (Gemini / Ollama)
         │
         ▼
      StrOutputParser
         │
         ▼
      answer (str)
    """
    store     = get_vectorstore(collection_name=collection_name)
    retriever = store.as_retriever(search_type="mmr", k=top_k)
    prompt    = get_rag_prompt()
    llm       = get_llm(temperature=0.0)

    chain = (
        {
            "context":  retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


def query_with_sources(
    question: str,
    collection_name: Optional[str] = None,
    top_k: int = 5,
) -> dict:
    """
    Run the RAG pipeline and return answer + source chunks.

    Returns:
        {
          "question": str,
          "answer": str,
          "sources": List[dict],   # page, type, content_preview, score
          "llm_provider": str,
          "model": str,
        }
    """
    from src.config.settings import get_settings
    settings = get_settings()

    store     = get_vectorstore(collection_name=collection_name)
    retriever = store.as_retriever(search_type="mmr", k=top_k)
    prompt    = get_rag_prompt()
    llm       = get_llm(temperature=0.0)

    # Retrieve source documents
    source_docs = retriever.invoke(question)

    # Format context and run through LLM
    context = format_docs(source_docs)
    messages = prompt.invoke({"question": question, "context": context})
    answer   = llm.invoke(messages).content.strip()

    # Build source list for response
    sources = []
    for doc in source_docs:
        meta = doc.metadata
        sources.append({
            "page":            meta.get("page", -1),
            "content_type":    meta.get("type", "unknown"),
            "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            "score":           meta.get("score"),
        })

    # Model name
    model_name = settings.gemini_model if settings.llm_provider == "gemini" else settings.ollama_model

    return {
        "question":      question,
        "answer":        answer,
        "sources":       sources,
        "llm_provider":  settings.llm_provider,
        "model":         model_name,
        "retrieval_method": "mmr",
    }
