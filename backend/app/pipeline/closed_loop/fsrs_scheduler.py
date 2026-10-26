import math
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.models import ReviewCard, Concept

logger = logging.getLogger(__name__)

class FSRSScheduler:
    """
    Step 15: Free Spaced Repetition Scheduler (FSRS).
    Calculates memory stability S, difficulty D, retrievability R,
    and schedules optimal spaced reviews using forgetting decay.
    """
    def compute_retrievability(self, elapsed_days: float, stability: float) -> float:
        """
        Forgetting curve: R(t, S) = (1 + t / (9 * S))^(-1)
        """
        if stability <= 0.01:
            return 0.1
        return (1.0 + (elapsed_days / (9.0 * stability))) ** -1.0

    def calculate_next_interval(
        self,
        rating: int,  # 1: Again, 2: Hard, 3: Good, 4: Easy
        current_stability: float,
        current_difficulty: float,
        reps: int
    ) -> Dict[str, float]:
        """
        FSRS update algorithm:
        """
        # Difficulty update:
        # D_new = D - w * (rating - 3)
        delta_d = -0.5 * (rating - 3)
        new_d = max(1.0, min(10.0, current_difficulty + delta_d))

        if rating == 1:  # Lapse / Again
            new_s = max(0.5, current_stability * 0.4)
            interval_days = 0.5  # Revisit in 12 hours
        elif rating == 2:  # Hard
            new_s = current_stability * 1.2
            interval_days = max(1.0, new_s * 0.8)
        elif rating == 3:  # Good
            new_s = current_stability * (1.0 + math.exp(2.0 - (new_d * 0.15)))
            interval_days = max(1.0, new_s)
        else:  # Easy
            new_s = current_stability * (1.5 + math.exp(2.5 - (new_d * 0.15)))
            interval_days = max(2.0, new_s * 1.3)

        return {
            "stability": round(new_s, 2),
            "difficulty": round(new_d, 2),
            "interval_days": round(interval_days, 1)
        }

    async def get_due_cards(self, user_id: str, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        res = await db.execute(
            select(ReviewCard).where(
                ReviewCard.user_id == user_id,
                ReviewCard.due_at <= now
            ).limit(limit)
        )
        cards = res.scalars().all()

        results = []
        for c in cards:
            elapsed = (now - (c.last_review_at or c.due_at)).days
            retrievability = self.compute_retrievability(max(0, elapsed), c.stability)
            results.append({
                "id": c.id,
                "concept_id": c.concept_id,
                "question": c.question,
                "answer": c.answer,
                "explanation": c.explanation,
                "stability": c.stability,
                "difficulty": c.difficulty,
                "retrievability": round(retrievability, 2),
                "reps": c.reps,
                "due_at": str(c.due_at)
            })

        return results

    async def record_review(
        self,
        card_id: str,
        rating: int,  # 1: Again, 2: Hard, 3: Good, 4: Easy
        db: AsyncSession
    ) -> Dict[str, Any]:
        res = await db.execute(select(ReviewCard).where(ReviewCard.id == card_id))
        card = res.scalars().first()
        if not card:
            raise ValueError(f"Card {card_id} not found")

        now = datetime.utcnow()
        calc = self.calculate_next_interval(
            rating=rating,
            current_stability=card.stability,
            current_difficulty=card.difficulty,
            reps=card.reps
        )

        card.stability = calc["stability"]
        card.difficulty = calc["difficulty"]
        card.reps += 1
        if rating == 1:
            card.lapses += 1
            card.state = 3  # Relearning
        else:
            card.state = 2  # Review

        card.last_review_at = now
        card.due_at = now + timedelta(days=calc["interval_days"])
        await db.commit()

        logger.info("FSRS review recorded for card %s: rating=%d, next_due in %.1f days",
                    card_id, rating, calc["interval_days"])

        return {
            "card_id": card.id,
            "new_stability": card.stability,
            "new_difficulty": card.difficulty,
            "interval_days": calc["interval_days"],
            "next_due_at": str(card.due_at)
        }

fsrs_scheduler = FSRSScheduler()
