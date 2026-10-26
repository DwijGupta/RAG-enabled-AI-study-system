import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.models import LearnerMastery, Concept, User
from app.core.graph_db import graph_store

logger = logging.getLogger(__name__)

# Standard BKT Default Parameters
BKT_P_L0 = 0.20  # Initial prior probability of knowing concept
BKT_P_T = 0.15   # Probability of learning (transit)
BKT_P_G = 0.20   # Probability of guessing correctly
BKT_P_S = 0.10   # Probability of slipping (knowing but making mistake)

class LearnerOverlay:
    """
    Step 2: Tracks long-term cognitive state, mastery per concept,
    and spreads updates along prerequisite graph edges using BKT.
    """
    async def get_mastery(self, user_id: str, concept_name: str, db: AsyncSession) -> Dict[str, Any]:
        """
        Retrieves current BKT mastery state for user & concept.
        Creates record if first time encountered.
        """
        c_clean = concept_name.strip()
        # Find concept in DB
        res = await db.execute(select(Concept).where(Concept.name.ilike(c_clean)))
        concept_obj = res.scalars().first()

        if not concept_obj:
            # Create on-the-fly concept record if discovered dynamically
            concept_obj = Concept(name=c_clean, description=f"Concept: {c_clean}")
            db.add(concept_obj)
            await db.commit()
            await db.refresh(concept_obj)

        # Check existing mastery record
        res_m = await db.execute(
            select(LearnerMastery).where(
                LearnerMastery.user_id == user_id,
                LearnerMastery.concept_id == concept_obj.id
            )
        )
        mastery_obj = res_m.scalars().first()

        if not mastery_obj:
            mastery_obj = LearnerMastery(
                user_id=user_id,
                concept_id=concept_obj.id,
                p_mastery=BKT_P_L0,
                uncertainty=0.40
            )
            db.add(mastery_obj)
            await db.commit()
            await db.refresh(mastery_obj)

        return {
            "concept_id": concept_obj.id,
            "concept_name": concept_obj.name,
            "p_mastery": round(mastery_obj.p_mastery, 3),
            "uncertainty": round(mastery_obj.uncertainty, 3),
            "total_attempts": mastery_obj.total_attempts,
            "correct_attempts": mastery_obj.correct_attempts,
            "hints_used": mastery_obj.hints_used,
            "active_misconceptions": mastery_obj.active_misconceptions or []
        }

    async def update_bkt(
        self,
        user_id: str,
        concept_name: str,
        is_correct: bool,
        used_hint: bool,
        db: AsyncSession
    ) -> float:
        """
        Applies Bayesian Knowledge Tracing Bayesian posterior update:
        P(L_t | obs) and transition P(L_t+1) = P(L_t|obs) + (1 - P(L_t|obs))*P(T).
        """
        state = await self.get_mastery(user_id, concept_name, db)
        p_prev = state["p_mastery"]
        p_g = BKT_P_G
        p_s = BKT_P_S
        p_t = BKT_P_T

        # If hint was used, discount correctness
        if is_correct and used_hint:
            p_g = 0.40

        if is_correct:
            numerator = p_prev * (1.0 - p_s)
            denominator = (p_prev * (1.0 - p_s)) + ((1.0 - p_prev) * p_g)
        else:
            numerator = p_prev * p_s
            denominator = (p_prev * p_s) + ((1.0 - p_prev) * (1.0 - p_g))

        p_posterior = numerator / max(1e-6, denominator)
        # Transit step
        p_updated = p_posterior + ((1.0 - p_posterior) * p_t)
        p_updated = max(0.01, min(0.99, p_updated))

        # Persist updated values in DB
        res_m = await db.execute(
            select(LearnerMastery).where(
                LearnerMastery.user_id == user_id,
                LearnerMastery.concept_id == state["concept_id"]
            )
        )
        record = res_m.scalars().first()
        if record:
            record.p_mastery = p_updated
            record.uncertainty = max(0.05, record.uncertainty * 0.85)
            record.total_attempts += 1
            if is_correct:
                record.correct_attempts += 1
            if used_hint:
                record.hints_used += 1
            await db.commit()

        # Prerequisite Mastery Spread:
        # If student succeeds on concept, upstream prerequisites receive reinforcement
        if is_correct:
            prereqs = graph_store.get_prerequisites(concept_name)
            for p_name in prereqs:
                await self._boost_prerequisite(user_id, p_name, db)

        logger.info("Updated BKT mastery for '%s': %.2f -> %.2f (obs=%s)",
                    concept_name, p_prev, p_updated, is_correct)
        return p_updated

    async def _boost_prerequisite(self, user_id: str, prereq_name: str, db: AsyncSession):
        """Mild Bayesian reinforcement boost for confirmed foundational prerequisite."""
        p_state = await self.get_mastery(user_id, prereq_name, db)
        curr_p = p_state["p_mastery"]
        boosted = min(0.99, curr_p + (1.0 - curr_p) * 0.10)
        
        res = await db.execute(
            select(LearnerMastery).where(
                LearnerMastery.user_id == user_id,
                LearnerMastery.concept_id == p_state["concept_id"]
            )
        )
        rec = res.scalars().first()
        if rec:
            rec.p_mastery = boosted
            await db.commit()

learner_overlay = LearnerOverlay()
