import os
import sys
import pytest
import asyncio

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.graph_db import graph_store
from app.pipeline.online.learner_overlay import learner_overlay
from app.pipeline.online.root_cause import root_cause_finder
from app.pipeline.online.planner import tutor_planner, TutorPlan
from app.pipeline.online.intent import StudentIntent
from app.pipeline.online.context_builder import context_builder
from app.pipeline.online.leak_filter import leak_filter
from app.pipeline.closed_loop.fsrs_scheduler import fsrs_scheduler
from app.core.db import AsyncSessionLocal, init_db

async def run_all_tests():
    print("\n--- 1. Testing Database & Graph Store Initialization ---")
    await init_db()
    
    # Seed sample prerequisite graph
    # Foundational: "Linear Algebra" -> "Matrix Multiplication" -> "Neural Network Layers" -> "Backpropagation"
    await graph_store.add_concept("Linear Algebra", description="Vectors, spaces, and linear transformations", difficulty=0.3)
    await graph_store.add_concept("Matrix Multiplication", description="Dot products and row-column transformations", difficulty=0.4)
    await graph_store.add_concept("Neural Network Layers", description="Weighted sum of inputs plus bias", difficulty=0.5)
    await graph_store.add_concept("Backpropagation", description="Chain rule gradient propagation", difficulty=0.7)

    await graph_store.add_prerequisite("Linear Algebra", "Matrix Multiplication")
    await graph_store.add_prerequisite("Matrix Multiplication", "Neural Network Layers")
    await graph_store.add_prerequisite("Neural Network Layers", "Backpropagation")

    # Add Misconception
    await graph_store.add_misconception(
        concept_name="Backpropagation",
        misconception_name="Gradient flows forward",
        description="Students confuse the forward pass output computation with backward gradient propagation.",
        refutation="Gradients propagate from loss backward toward earlier layers using the calculus chain rule."
    )

    prereqs = graph_store.get_prerequisites("Backpropagation")
    print(f"Prerequisites of Backpropagation: {prereqs}")
    assert "Neural Network Layers" in prereqs, "Prerequisite link check failed"

    tree = graph_store.get_full_prerequisite_tree("Backpropagation")
    print(f"Full Prerequisite Tree depth: {len(tree)} nodes traversed")
    assert len(tree) >= 3, "Prerequisite graph traversal failed"

    print("\n--- 2. Testing Bayesian Knowledge Tracing (BKT) ---")
    async with AsyncSessionLocal() as db:
        user_id = "test_student_42"
        # Initial mastery
        m0 = await learner_overlay.get_mastery(user_id, "Matrix Multiplication", db)
        print(f"Initial P(L): {m0['p_mastery']}")
        
        # Correct answer update
        m1 = await learner_overlay.update_bkt(user_id, "Matrix Multiplication", is_correct=True, used_hint=False, db=db)
        print(f"Updated P(L) after correct: {m1}")
        assert m1 > m0['p_mastery'], "BKT correctness boost failed"

        # Incorrect answer update
        m2 = await learner_overlay.update_bkt(user_id, "Matrix Multiplication", is_correct=False, used_hint=False, db=db)
        print(f"Updated P(L) after incorrect: {m2}")
        assert m2 < m1, "BKT penalty on incorrect failed"

    print("\n--- 3. Testing Cognitive Root-Cause Finder ---")
    async with AsyncSessionLocal() as db:
        # Student asks about Backpropagation, but has never mastered Linear Algebra
        root = await root_cause_finder.find_root_cause(user_id, ["Backpropagation"], db)
        print(f"Root cause diagnosed: {root['weakest_concept']} (Mastery: {root['mastery_score']})")
        assert root["has_weakness"] is True, "Root cause detection should find weak foundational node"

    print("\n--- 4. Testing Tutor Planner Strategy Selection ---")
    ped_ctx = context_builder.build_context(
        reranked_chunks=[{"id": "c1", "content": "Backpropagation computes chain rule gradients.", "page_number": 12}],
        root_cause_result=root,
        learner_mastery=0.25,
        session_turns=[],
        past_traces=[]
    )
    intent = StudentIntent(
        question_type="conceptual_question",
        target_concepts=["Backpropagation"],
        learning_goal="Understand backpropagation",
        complexity_level=0.7
    )
    plan = tutor_planner.plan(intent, ped_ctx, root)
    print(f"Tutor Planner Action: {plan.action} - Rationale: {plan.rationale}")
    assert plan.action in ["REMEDIATE", "EXPLAIN"], "Planner should remediate prerequisite gap"

    print("\n--- 5. Testing Leak Filter & Output Sanitizer ---")
    raw_leaked_text = (
        "=== PEDAGOGICAL PLAN ===\nAction: EXPLAIN\nDirective: Be nice\n\n"
        "Here is the answer based on [REF-1]. Gradients flow backward."
    )
    clean_text = leak_filter.sanitize(raw_leaked_text)
    print(f"Sanitized Text: '{clean_text}'")
    assert "=== PEDAGOGICAL PLAN ===" not in clean_text, "Leak filter failed to remove internal prompt"
    assert "[Doc 1]" in clean_text, "Leak filter failed to format citation badge"

    print("\n--- 6. Testing FSRS Spaced Repetition Calculations ---")
    # Rating 3: Good
    fsrs_result = fsrs_scheduler.calculate_next_interval(rating=3, current_stability=2.0, current_difficulty=5.0, reps=1)
    print(f"FSRS Good Rating: Stability={fsrs_result['stability']}, Interval={fsrs_result['interval_days']} days")
    assert fsrs_result['interval_days'] >= 1.0, "Interval calculation error"

    # Forgetting curve retrievability after 10 days
    r = fsrs_scheduler.compute_retrievability(elapsed_days=10, stability=fsrs_result['stability'])
    print(f"Retrievability R(10d): {r:.2%}")
    assert 0.0 < r < 1.0, "Forgetting curve retrievability bounds error"

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<\n")
    from app.core.db import engine
    await engine.dispose()

def test_pipeline_suite():
    """Pytest suite runner for BKT, Root-Cause, Planner, Leak Filter, and FSRS."""
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    asyncio.run(run_all_tests())
