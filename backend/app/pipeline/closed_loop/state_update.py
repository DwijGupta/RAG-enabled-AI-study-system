import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.pipeline.online.learner_overlay import learner_overlay
from app.pipeline.closed_loop.assessment import AssessmentEvaluation

logger = logging.getLogger(__name__)

class StateUpdateCoordinator:
    """
    Step 14: Closed-loop state updater.
    Takes assessment evaluation results, feeds back into BKT learner overlay,
    updates concept mastery, and records misconceptions.
    """
    async def process_assessment_result(
        self,
        user_id: str,
        concept_name: str,
        evaluation: AssessmentEvaluation,
        used_hint: bool,
        db: AsyncSession
    ) -> Dict[str, Any]:
        # 1. Update BKT mastery
        new_mastery = await learner_overlay.update_bkt(
            user_id=user_id,
            concept_name=concept_name,
            is_correct=evaluation.is_correct,
            used_hint=used_hint,
            db=db
        )

        logger.info(
            "Closed-loop state updated for user %s on '%s': new_p=%.2f, correct=%s",
            user_id, concept_name, new_mastery, evaluation.is_correct
        )

        return {
            "concept_name": concept_name,
            "new_mastery": new_mastery,
            "is_correct": evaluation.is_correct,
            "identified_misconception": evaluation.identified_misconception,
            "feedback": evaluation.feedback,
            "recommended_remedy": evaluation.recommended_remedy
        }

state_updater = StateUpdateCoordinator()
