import pytest
from app.core.config import settings
from app.pipeline.online.leak_filter import leak_filter
from app.pipeline.closed_loop.fsrs_scheduler import fsrs_scheduler
from app.pipeline.online.planner import tutor_planner
from app.pipeline.online.intent import StudentIntent
from app.pipeline.online.context_builder import context_builder

def test_settings_loaded():
    """Verify settings defaults and types."""
    assert settings.PROJECT_NAME is not None
    assert settings.VERSION == "1.0.0"
    assert "sqlite" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL

def test_leak_filter_prompt_leakage():
    """Verify internal chain-of-thought and prompt instructions are sanitized."""
    raw_text = (
        "=== PEDAGOGICAL PLAN ===\n"
        "Action: REMEDIATE\n"
        "Directives: Do not give the direct answer\n\n"
        "A vector space is a set of elements called vectors. See [REF-1]."
    )
    sanitized = leak_filter.sanitize(raw_text)
    assert "=== PEDAGOGICAL PLAN ===" not in sanitized
    assert "Directives:" not in sanitized
    assert "[Doc 1]" in sanitized
    assert "vector space" in sanitized

def test_fsrs_intervals():
    """Verify spaced repetition scheduler math."""
    # Good rating (3)
    res_good = fsrs_scheduler.calculate_next_interval(rating=3, current_stability=2.0, current_difficulty=5.0, reps=1)
    assert res_good["interval_days"] >= 1.0
    assert res_good["stability"] > 2.0

    # Hard rating (2)
    res_hard = fsrs_scheduler.calculate_next_interval(rating=2, current_stability=2.0, current_difficulty=5.0, reps=1)
    assert res_hard["stability"] <= res_good["stability"]

    # Retrievability forgetting curve calculation
    retrievability = fsrs_scheduler.compute_retrievability(elapsed_days=5, stability=10.0)
    assert 0.0 < retrievability <= 1.0

def test_tutor_planner_remediation():
    """Verify planner recommends REMEDIATE when foundational prerequisite weakness exists."""
    intent = StudentIntent(
        question_type="conceptual_question",
        target_concepts=["Backpropagation"],
        learning_goal="Understand gradient descent",
        complexity_level=0.7
    )
    root_cause = {
        "has_weakness": True,
        "weakest_concept": "Matrix Multiplication",
        "mastery_score": 0.35,
        "depth": 2,
        "is_direct_target": False,
        "path": ["Backpropagation", "Neural Network Layers", "Matrix Multiplication"],
        "active_misconceptions": []
    }
    context = context_builder.build_context(
        reranked_chunks=[],
        root_cause_result=root_cause,
        learner_mastery=0.35,
        session_turns=[],
        past_traces=[]
    )
    plan = tutor_planner.plan(intent, context, root_cause)
    assert plan.action == "REMEDIATE"
    assert "Matrix Multiplication" in plan.rationale
