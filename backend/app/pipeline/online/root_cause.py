import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.graph_db import graph_store
from app.pipeline.online.learner_overlay import learner_overlay

logger = logging.getLogger(__name__)

MASTERY_DEFICIENCY_THRESHOLD = 0.65

class RootCauseFinder:
    """
    Step 4: Prerequisite graph traversal to identify cognitive root-cause weaknesses
    and active misconceptions.
    """
    async def find_root_cause(
        self,
        user_id: str,
        target_concepts: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Traverses upstream prerequisites for all target concepts.
        Finds the earliest/deepest unmastered prerequisite (weakest node).
        """
        if not target_concepts:
            return {
                "has_weakness": False,
                "weakest_concept": None,
                "mastery_score": 1.0,
                "path": [],
                "active_misconceptions": []
            }

        candidate_weaknesses = []

        for target in target_concepts:
            # 1. Check target concept mastery itself
            target_mastery = await learner_overlay.get_mastery(user_id, target, db)
            candidate_weaknesses.append({
                "concept": target,
                "p_mastery": target_mastery["p_mastery"],
                "depth": 0,
                "is_direct_target": True
            })

            # 2. Get prerequisite dependency tree
            prereq_tree = graph_store.get_full_prerequisite_tree(target, max_depth=4)
            for node in prereq_tree:
                prereq_name = node["concept"]
                if prereq_name == target:
                    continue
                p_state = await learner_overlay.get_mastery(user_id, prereq_name, db)
                candidate_weaknesses.append({
                    "concept": prereq_name,
                    "p_mastery": p_state["p_mastery"],
                    "depth": node["depth"],
                    "is_direct_target": False
                })

        # Filter below threshold
        weak_nodes = [w for w in candidate_weaknesses if w["p_mastery"] < MASTERY_DEFICIENCY_THRESHOLD]

        if not weak_nodes:
            return {
                "has_weakness": False,
                "weakest_concept": None,
                "mastery_score": 1.0,
                "path": [],
                "active_misconceptions": []
            }

        # Sort by: 1) depth descending (foundational prerequisites first), 2) lowest mastery
        weak_nodes.sort(key=lambda x: (-x["depth"], x["p_mastery"]))
        weakest = weak_nodes[0]

        # Retrieve any known misconceptions for this weak node
        misconceptions = graph_store.get_misconceptions(weakest["concept"])

        logger.info("Diagnosed root-cause: '%s' (depth=%d, mastery=%.2f)",
                    weakest["concept"], weakest["depth"], weakest["p_mastery"])

        return {
            "has_weakness": True,
            "weakest_concept": weakest["concept"],
            "mastery_score": weakest["p_mastery"],
            "depth": weakest["depth"],
            "is_direct_target": weakest["is_direct_target"],
            "path": [w["concept"] for w in weak_nodes],
            "active_misconceptions": misconceptions
        }

root_cause_finder = RootCauseFinder()
