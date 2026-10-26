import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.pipeline.closed_loop.assessment import assessment_engine
from app.pipeline.closed_loop.state_update import state_updater

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assessment", tags=["Practice Assessment & Grading"])

class GenerateQuizRequest(BaseModel):
    concept_name: str
    difficulty: float = 0.5

class SubmitQuizRequest(BaseModel):
    user_id: str = "student_1"
    concept_name: str
    question_text: str
    student_answer: str
    correct_answer: str
    used_hint: bool = False

@router.post("/generate")
async def generate_quiz(req: GenerateQuizRequest):
    question = await assessment_engine.generate_diagnostic_question(
        concept_name=req.concept_name,
        difficulty=req.difficulty
    )
    return question.model_dump()

@router.post("/submit")
async def submit_quiz(req: SubmitQuizRequest, db: AsyncSession = Depends(get_db)):
    evaluation = await assessment_engine.evaluate_answer(
        question=req.question_text,
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        concept_name=req.concept_name
    )

    update_summary = await state_updater.process_assessment_result(
        user_id=req.user_id,
        concept_name=req.concept_name,
        evaluation=evaluation,
        used_hint=req.used_hint,
        db=db
    )

    return {
        "evaluation": evaluation.model_dump(),
        "state_update": update_summary
    }
