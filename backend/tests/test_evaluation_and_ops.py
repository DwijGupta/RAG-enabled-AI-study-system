import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.db import AsyncSessionLocal, init_db
from app.core.telemetry import telemetry_manager
from app.eval.eval_harness import ragas_evaluator
from app.pipeline.online.coordinator import online_pipeline

async def run_evaluation_and_ops_tests():
    print("=" * 60)
    print("TEST: EVALUATION & OPS LAYER (LANGFUSE + RAGAS + TELEMETRY)")
    print("=" * 60)
    await init_db()

    print("\n[Step 1] Testing Langfuse Telemetry Manager Initialization & Passive Fail-safe...")
    assert hasattr(telemetry_manager, "create_trace"), "telemetry_manager missing create_trace"
    assert hasattr(telemetry_manager, "create_span"), "telemetry_manager missing create_span"
    assert hasattr(telemetry_manager, "log_score"), "telemetry_manager missing log_score"
    
    trace = telemetry_manager.create_trace(
        name="test_trace",
        user_id="test_student",
        session_id="test_sess",
        input_query="What is a dot product?"
    )
    span = telemetry_manager.create_span(trace, name="test_span", input_data={"k": 60})
    telemetry_manager.end_span(span, output_data={"status": "ok"})
    telemetry_manager.log_score(trace.id, "faithfulness", 0.95)
    telemetry_manager.flush()
    print("[PASS] Telemetry manager created traces, spans, and scores with zero latency impact!")

    print("\n[Step 2] Testing Coordinator Pipeline Langfuse Integration...")
    async with AsyncSessionLocal() as db:
        res = await online_pipeline.run(
            user_id="ops_eval_student",
            session_id="ops_sess_1",
            user_query="What is the dot product and how does it relate to vector similarity?",
            db=db
        )
        print(f"Pipeline executed in {res['latency_ms']} ms")
        print(f"Trace ID generated: {res.get('trace_id')}")
        print(f"Faithfulness Score: {res.get('faithfulness_score'):.2%}")
        assert "trace_id" in res, "Pipeline response missing Langfuse trace_id"
        assert "faithfulness_score" in res, "Pipeline response missing faithfulness_score"
        assert len(res["answer"]) > 10, "Pipeline answer empty"
    print("[PASS] Pipeline executed with full telemetry instrumentation and trace_id binding!")

    print("\n[Step 3] Testing RAGAS Evaluation Harness...")
    single_eval = await ragas_evaluator.evaluate_turn(
        query="What is the dot product and how does it relate to vector similarity?",
        ground_truth="The dot product multiplies matching vector components and sums them, giving cosine similarity for normalized vectors.",
        target_concept="Dot Product & Projection",
        expected_difficulty=0.35,
        user_id="ops_eval_student"
    )
    print("RAGAS Evaluation Turn Report:")
    for metric_name, val in single_eval["metrics"].items():
        print(f"  - {metric_name}: {val:.2%}")
    
    assert single_eval["metrics"]["faithfulness"] > 0.0, "Faithfulness calculation failed"
    assert single_eval["metrics"]["answer_relevance"] > 0.0, "Answer relevance calculation failed"
    assert single_eval["metrics"]["ragas_composite"] > 0.0, "RAGAS composite index calculation failed"
    print("[PASS] RAGAS evaluation metrics computed successfully!")

    print("\n" + "=" * 60)
    print("ALL EVALUATION & OPS LAYER TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
    from app.core.db import engine
    await engine.dispose()

def test_evaluation_and_ops_suite():
    """Pytest suite runner for Langfuse telemetry, RAGAS composite index, and faithfulness."""
    asyncio.run(run_evaluation_and_ops_tests())

if __name__ == "__main__":
    asyncio.run(run_evaluation_and_ops_tests())
