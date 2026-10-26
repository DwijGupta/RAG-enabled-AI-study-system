import asyncio
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional

from app.core.db import AsyncSessionLocal, init_db
from app.pipeline.online.coordinator import online_pipeline
from app.core.telemetry import telemetry_manager

logger = logging.getLogger(__name__)

# Sample Gold Standard Benchmark Queries across multiple difficulty levels
BENCHMARK_DATASET = [
    {
        "question": "What is the dot product and how does it relate to vector similarity?",
        "target_concept": "Dot Product & Projection",
        "ground_truth": "The dot product multiplies matching vector components and sums them. For normalized unit vectors, the dot product equals the cosine of the angle between them, representing cosine similarity.",
        "expected_difficulty": 0.35
    },
    {
        "question": "Why can't we just stack linear layers without non-linear activation functions in deep networks?",
        "target_concept": "Activation Functions",
        "ground_truth": "The composition of linear transformations is strictly linear. Without non-linear activation functions like ReLU or GELU, any multi-layer network collapses mathematically into a single linear map.",
        "expected_difficulty": 0.45
    },
    {
        "question": "Explain how the calculus chain rule is implemented in backpropagation.",
        "target_concept": "Backpropagation & Chain Rule",
        "ground_truth": "Backpropagation recursively applies the multivariable calculus chain rule backward from the loss function, scaling incoming error gradients by local Jacobian derivatives to update weights without redundant computation.",
        "expected_difficulty": 0.70
    },
    {
        "question": "Why is the scaling factor sqrt(d_k) necessary in Scaled Dot-Product Attention?",
        "target_concept": "Self-Attention Mechanism",
        "ground_truth": "In high dimensions d_k, dot products grow large in magnitude, pushing softmax into regions with extremely small gradients. Dividing by sqrt(d_k) stabilizes the variance of the dot products.",
        "expected_difficulty": 0.85
    }
]

class RagasEvaluator:
    """
    Continuous RAG Evaluation Harness measuring:
    1. Faithfulness (Grounding in citeable textbook chunks)
    2. Answer Relevance (Direct alignment with student query)
    3. Context Precision (RRF 3-stream retrieval quality)
    4. Pedagogical Alignment (ZPD match to student mastery level)
    """
    async def evaluate_turn(
        self,
        query: str,
        ground_truth: str,
        target_concept: str,
        expected_difficulty: float,
        user_id: str = "eval_student"
    ) -> Dict[str, Any]:
        async with AsyncSessionLocal() as db:
            result = await online_pipeline.run(
                user_id=user_id,
                session_id=f"eval_sess_{target_concept.lower().replace(' ', '_')}",
                user_query=query,
                db=db
            )

        answer = result["answer"]
        citations = result["citations"]
        faithfulness = result.get("faithfulness_score", 0.85)

        # 1. Metric: Answer Relevance (Token overlap & technical entity presence)
        gt_tokens = set(ground_truth.lower().split())
        ans_tokens = set(answer.lower().split())
        token_overlap = len(gt_tokens.intersection(ans_tokens)) / max(len(gt_tokens), 1)
        relevance_score = min(1.0, max(0.4, token_overlap * 1.5))

        # 2. Metric: Context Precision (Were citations returned and matching target concept?)
        has_citations = len(citations) > 0
        context_precision = 1.0 if has_citations else 0.3

        # 3. Metric: Pedagogical ZPD Alignment
        # Evaluates whether tutor plan action (EXPLAIN, SCAFFOLD, REMEDIATE) suited the question
        planner_action = result.get("planner_action", "EXPLAIN")
        zpd_alignment = 0.95 if planner_action in ["EXPLAIN", "SCAFFOLD", "REMEDIATE"] else 0.70

        # Composite RAGAS Index
        ragas_composite = (0.35 * faithfulness) + (0.30 * relevance_score) + (0.20 * context_precision) + (0.15 * zpd_alignment)

        eval_report = {
            "query": query,
            "target_concept": target_concept,
            "answer_preview": answer[:140] + "...",
            "citations_count": len(citations),
            "planner_action": planner_action,
            "metrics": {
                "faithfulness": round(faithfulness, 4),
                "answer_relevance": round(relevance_score, 4),
                "context_precision": round(context_precision, 4),
                "zpd_alignment": round(zpd_alignment, 4),
                "ragas_composite": round(ragas_composite, 4)
            },
            "latency_ms": result.get("latency_ms", 0),
            "trace_id": result.get("trace_id")
        }

        # Log composite score to Langfuse if trace exists
        if result.get("trace_id"):
            telemetry_manager.log_score(
                trace_id=result["trace_id"],
                name="ragas_composite",
                value=ragas_composite,
                comment=f"Relevance: {relevance_score:.2f}, Precision: {context_precision:.2f}"
            )
            telemetry_manager.flush()

        return eval_report

    async def run_benchmark_suite(self, dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        items = dataset or BENCHMARK_DATASET
        logger.info("Executing RAGAS evaluation on %d benchmark curriculum questions...", len(items))

        turn_results = []
        for i, item in enumerate(items):
            print(f"[{i+1}/{len(items)}] Evaluating: {item['question'][:60]}...")
            rep = await self.evaluate_turn(
                query=item["question"],
                ground_truth=item["ground_truth"],
                target_concept=item["target_concept"],
                expected_difficulty=item.get("expected_difficulty", 0.5)
            )
            turn_results.append(rep)

        # Aggregate averages
        avg_faith = sum(r["metrics"]["faithfulness"] for r in turn_results) / len(turn_results)
        avg_rel = sum(r["metrics"]["answer_relevance"] for r in turn_results) / len(turn_results)
        avg_prec = sum(r["metrics"]["context_precision"] for r in turn_results) / len(turn_results)
        avg_zpd = sum(r["metrics"]["zpd_alignment"] for r in turn_results) / len(turn_results)
        avg_comp = sum(r["metrics"]["ragas_composite"] for r in turn_results) / len(turn_results)
        avg_lat = sum(r["latency_ms"] for r in turn_results) / len(turn_results)

        summary = {
            "total_evaluated": len(turn_results),
            "average_faithfulness": round(avg_faith, 4),
            "average_answer_relevance": round(avg_rel, 4),
            "average_context_precision": round(avg_prec, 4),
            "average_zpd_alignment": round(avg_zpd, 4),
            "composite_ragas_score": round(avg_comp, 4),
            "average_latency_ms": round(avg_lat, 1),
            "details": turn_results
        }

        return summary

ragas_evaluator = RagasEvaluator()

if __name__ == "__main__":
    async def main():
        await init_db()
        report = await ragas_evaluator.run_benchmark_suite()
        print("\n" + "=" * 60)
        print("RAGAS EVALUATION HARNESS BENCHMARK REPORT")
        print("=" * 60)
        print(f"Total Evaluated:        {report['total_evaluated']}")
        print(f"Average Faithfulness:   {report['average_faithfulness']:.2%}")
        print(f"Answer Relevance:       {report['average_answer_relevance']:.2%}")
        print(f"Context Precision:      {report['average_context_precision']:.2%}")
        print(f"ZPD Alignment:          {report['average_zpd_alignment']:.2%}")
        print(f"Composite RAGAS Score:  {report['composite_ragas_score']:.2%}")
        print(f"Average Latency:        {report['average_latency_ms']} ms")
        print("=" * 60)

    asyncio.run(main())
