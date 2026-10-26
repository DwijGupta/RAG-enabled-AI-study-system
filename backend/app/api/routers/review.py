import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.models import ReviewCard
from app.pipeline.closed_loop.fsrs_scheduler import fsrs_scheduler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/review", tags=["FSRS Spaced Repetition Deck"])

class RateCardRequest(BaseModel):
    card_id: str
    rating: int # 1: Again, 2: Hard, 3: Good, 4: Easy

class CreateCardRequest(BaseModel):
    user_id: str = "student_1"
    concept_id: str
    question: str
    answer: str
    explanation: str = ""

@router.get("/due")
async def get_due_cards(
    user_id: str = Query("student_1"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    cards = await fsrs_scheduler.get_due_cards(user_id=user_id, db=db, limit=limit)
    return {"due_cards": cards, "count": len(cards)}

@router.post("/rate")
async def rate_card(req: RateCardRequest, db: AsyncSession = Depends(get_db)):
    if req.rating not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Rating must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)")
    
    result = await fsrs_scheduler.record_review(
        card_id=req.card_id,
        rating=req.rating,
        db=db
    )
    return result

@router.post("/create")
async def create_card(req: CreateCardRequest, db: AsyncSession = Depends(get_db)):
    card = ReviewCard(
        user_id=req.user_id,
        concept_id=req.concept_id,
        question=req.question,
        answer=req.answer,
        explanation=req.explanation
    )
    db.add(card)
    await db.commit()
    await db.refresh(card)
    return {"status": "created", "card_id": card.id}
