"""
api/routes/evaluate.py — POST /evaluate endpoint (fully wired).
"""
from fastapi import APIRouter, HTTPException
from api.schemas.evaluate import EvaluateRequest, EvaluateResponse, PerQuestionResult

router = APIRouter()


@router.post("", response_model=EvaluateResponse, summary="Run RAGAS evaluation")
async def evaluate_rag(request: EvaluateRequest):
    """
    Run RAGAS evaluation (faithfulness, answer_relevancy,
    context_precision, context_recall) on provided Q&A pairs.
    """
    try:
        from src.evaluation.evaluator import run_evaluation

        qa_pairs = [
            {"question": qa.question, "ground_truth": qa.ground_truth}
            for qa in request.qa_pairs
        ]

        result = run_evaluation(
            qa_pairs=qa_pairs,
            collection_name=request.collection_name,
            top_k=request.top_k,
        )

        details = [
            PerQuestionResult(
                question=d["question"],
                answer=d["answer"],
                ground_truth=d["ground_truth"],
                faithfulness=d.get("faithfulness"),
                answer_relevancy=d.get("answer_relevancy"),
                context_precision=d.get("context_precision"),
                context_recall=d.get("context_recall"),
            )
            for d in result["details"]
        ]

        return EvaluateResponse(
            faithfulness=result["faithfulness"],
            answer_relevancy=result["answer_relevancy"],
            context_precision=result["context_precision"],
            context_recall=result["context_recall"],
            details=details,
            llm_provider=result["llm_provider"],
            num_questions=result["num_questions"],
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
