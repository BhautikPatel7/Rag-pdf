"""
src/evaluation/evaluator.py
RAGAS evaluation runner.
Takes a list of {question, ground_truth} pairs, runs the RAG pipeline,
and scores the results using RAGAS metrics.
"""
from typing import List, Dict, Any, Optional

from src.config.settings import get_settings
from src.rag.pipeline import query_with_sources


def run_evaluation(
    qa_pairs: List[Dict[str, str]],
    collection_name: Optional[str] = None,
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Run RAGAS evaluation on a list of Q&A pairs.

    Args:
        qa_pairs: List of {"question": str, "ground_truth": str}
        collection_name: Optional override for vector store collection
        top_k: Number of chunks to retrieve per question

    Returns:
        {
          "faithfulness": float,
          "answer_relevancy": float,
          "context_precision": float,
          "context_recall": float,
          "details": [...per-question results...],
          "llm_provider": str,
          "num_questions": int,
        }
    """
    settings = get_settings()

    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from datasets import Dataset

    # ── Step 1: Run RAG pipeline for each question ─────────────────────────────
    questions     = []
    answers       = []
    contexts      = []
    ground_truths = []
    per_question  = []

    print(f"Running RAG pipeline for {len(qa_pairs)} questions...")

    for qa in qa_pairs:
        question     = qa["question"]
        ground_truth = qa["ground_truth"]

        result = query_with_sources(
            question=question,
            collection_name=collection_name,
            top_k=top_k,
        )

        answer  = result["answer"]
        sources = result["sources"]

        # RAGAS expects contexts as List[str] per question
        ctx_texts = [s["content_preview"] for s in sources]

        questions.append(question)
        answers.append(answer)
        contexts.append(ctx_texts)
        ground_truths.append(ground_truth)

        per_question.append({
            "question":     question,
            "answer":       answer,
            "ground_truth": ground_truth,
        })

        print(f"  ✓ {question[:60]}...")

    # ── Step 2: Build RAGAS Dataset ────────────────────────────────────────────
    dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    })

    # ── Step 3: Configure RAGAS LLM ───────────────────────────────────────────
    # RAGAS uses its own LLM for judging — we wire it to our configured provider
    metrics = []
    if settings.ragas_faithfulness:
        metrics.append(faithfulness)
    if settings.ragas_answer_relevancy:
        metrics.append(answer_relevancy)
    if settings.ragas_context_precision:
        metrics.append(context_precision)
    if settings.ragas_context_recall:
        metrics.append(context_recall)

    # Configure RAGAS to use our LLM
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper

        ragas_llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
        ))
        ragas_emb = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.gemini_api_key,
        ))
        for m in metrics:
            m.llm = ragas_llm
            if hasattr(m, "embeddings"):
                m.embeddings = ragas_emb

    elif settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        from ragas.llms import LangchainLLMWrapper
        ragas_llm = LangchainLLMWrapper(ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        ))
        for m in metrics:
            m.llm = ragas_llm

    # ── Step 4: Run RAGAS ──────────────────────────────────────────────────────
    print("Running RAGAS evaluation...")
    results = evaluate(dataset=dataset, metrics=metrics)
    scores  = results.to_pandas()

    # ── Step 5: Merge per-question scores ─────────────────────────────────────
    for i, row in enumerate(per_question):
        if i < len(scores):
            row["faithfulness"]       = float(scores.iloc[i].get("faithfulness",       0.0) or 0.0)
            row["answer_relevancy"]   = float(scores.iloc[i].get("answer_relevancy",   0.0) or 0.0)
            row["context_precision"]  = float(scores.iloc[i].get("context_precision",  0.0) or 0.0)
            row["context_recall"]     = float(scores.iloc[i].get("context_recall",     0.0) or 0.0)

    def _avg(col: str) -> float:
        vals = [r.get(col, 0.0) or 0.0 for r in per_question]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    return {
        "faithfulness":      _avg("faithfulness"),
        "answer_relevancy":  _avg("answer_relevancy"),
        "context_precision": _avg("context_precision"),
        "context_recall":    _avg("context_recall"),
        "details":           per_question,
        "llm_provider":      settings.llm_provider,
        "num_questions":     len(qa_pairs),
    }
