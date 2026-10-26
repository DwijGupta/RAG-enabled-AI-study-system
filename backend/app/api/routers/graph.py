import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.core.graph_db import graph_store
from app.core.models import LearnerMastery, Concept

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph", tags=["Concept Graph & Mastery Visualizer"])

@router.get("/data")
async def get_graph_data(
    user_id: str = Query("student_1"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns graph nodes and prerequisite edges enriched with the user's
    real-time BKT mastery probabilities for 2D visual layout.
    """
    raw_data = graph_store.get_all_graph_data()
    
    # Fetch user masteries for all concepts
    res = await db.execute(select(LearnerMastery).where(LearnerMastery.user_id == user_id))
    mastery_records = res.scalars().all()
    mastery_by_concept_id = {m.concept_id: m for m in mastery_records}

    # Fetch concept ID by name
    res_c = await db.execute(select(Concept))
    concepts = res_c.scalars().all()
    concept_map = {c.name.lower(): c for c in concepts}

    enriched_nodes = []
    for n in raw_data["nodes"]:
        name_lower = n["id"].lower()
        p_mastery = 0.20 # default prior
        attempts = 0
        
        if name_lower in concept_map:
            c_obj = concept_map[name_lower]
            if c_obj.id in mastery_by_concept_id:
                m_obj = mastery_by_concept_id[c_obj.id]
                p_mastery = m_obj.p_mastery
                attempts = m_obj.total_attempts

        # Compute status color tag: Weak (<0.45), Developing/ZPD (0.45-0.75), Mastered (>0.75)
        if p_mastery >= 0.75:
            status = "mastered"
            color = "#10B981" # Emerald Green
        elif p_mastery >= 0.45:
            status = "developing"
            color = "#F59E0B" # Amber (in ZPD)
        else:
            status = "needs_practice"
            color = "#EF4444" # Coral Red

        if n.get("type") == "misconception":
            color = "#8B5CF6" # Violet for misconception
            status = "misconception"

        enriched_nodes.append({
            "id": n["id"],
            "label": n["label"],
            "type": n.get("type", "concept"),
            "description": n.get("description", ""),
            "domain": n.get("domain", "General"),
            "difficulty": n.get("difficulty", 0.5),
            "p_mastery": round(p_mastery, 2),
            "total_attempts": attempts,
            "status": status,
            "color": color
        })

    return {
        "nodes": enriched_nodes,
        "edges": raw_data["edges"],
        "total_nodes": len(enriched_nodes),
        "total_edges": len(raw_data["edges"])
    }
