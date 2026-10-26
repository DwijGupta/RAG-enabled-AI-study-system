import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.db import get_db
from app.core.models import LearnerMastery, Concept, InteractionTrace

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/learner", tags=["Learner Overlay Profile"])

@router.get("/profile")
async def get_learner_profile(
    user_id: str = Query("student_1"),
    db: AsyncSession = Depends(get_db)
):
    # Fetch masteries
    res = await db.execute(
        select(LearnerMastery, Concept.name)
        .join(Concept, LearnerMastery.concept_id == Concept.id)
        .where(LearnerMastery.user_id == user_id)
    )
    records = res.all()

    total_concepts = len(records)
    mastered = sum(1 for m, _ in records if m.p_mastery >= 0.75)
    in_zpd = sum(1 for m, _ in records if 0.45 <= m.p_mastery < 0.75)
    needs_work = sum(1 for m, _ in records if m.p_mastery < 0.45)
    
    avg_mastery = (
        sum(m.p_mastery for m, _ in records) / max(1, total_concepts)
        if total_concepts > 0 else 0.20
    )

    concept_breakdown = [
        {
            "concept_name": name,
            "p_mastery": round(m.p_mastery, 2),
            "uncertainty": round(m.uncertainty, 2),
            "attempts": m.total_attempts,
            "correct": m.correct_attempts,
            "last_practiced": str(m.last_practiced_at)
        }
        for m, name in records
    ]

    # Fetch recent traces
    res_t = await db.execute(
        select(InteractionTrace)
        .where(InteractionTrace.user_id == user_id)
        .order_by(InteractionTrace.created_at.desc())
        .limit(5)
    )
    recent_traces = res_t.scalars().all()

    return {
        "user_id": user_id,
        "total_concepts_tracked": total_concepts,
        "mastered_count": mastered,
        "in_zpd_count": in_zpd,
        "needs_work_count": needs_work,
        "overall_mastery": round(avg_mastery, 2),
        "concepts": concept_breakdown,
        "recent_traces": [
            {
                "id": t.id,
                "query": t.user_query,
                "planner_action": t.planner_action,
                "diagnosed_weakness": t.diagnosed_weak_concept,
                "faithfulness": t.faithfulness_score,
                "created_at": str(t.created_at)
            }
            for t in recent_traces
        ]
    }
