import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.ollama_client import ollama_client
from app.core.graph_db import graph_store

logger = logging.getLogger(__name__)

class PracticeQuestion(BaseModel):
    concept_name: str
    question_text: str
    options: List[str] = Field(description="4 multiple-choice options or empty for open-ended.")
    correct_option_index: int = Field(default=0, description="0-indexed correct option.")
    explanation: str = Field(description="Explanation of why this answer is correct and why other options are common traps.")
    hints: List[str] = Field(default_factory=list, description="Graduated hints for scaffolding.")

class AssessmentEvaluation(BaseModel):
    is_correct: bool
    score: float = Field(description="Score between 0.0 and 1.0.")
    feedback: str = Field(description="Empathetic, clear diagnostic feedback.")
    identified_misconception: Optional[str] = Field(default=None, description="If student made an error, which misconception was triggered?")
    recommended_remedy: str = Field(description="Guidance on what to review or practice next.")

class AssessmentEngine:
    """
    Step 13: Generates diagnostic questions and grades student responses with a rubric.
    """
    async def generate_diagnostic_question(
        self,
        concept_name: str,
        difficulty: float = 0.5
    ) -> PracticeQuestion:
        # Check if known misconceptions exist to craft effective distractors
        misconceptions = graph_store.get_misconceptions(concept_name)
        misc_str = "\n".join([f"- Trap: {m['name']}: {m['description']}" for m in misconceptions])

        prompt = (
            f"Concept: {concept_name}\n"
            f"Target Difficulty: {difficulty:.1f} (0.1 easy, 1.0 advanced)\n"
            f"Known Student Misconceptions to test for:\n{misc_str or 'None known'}\n\n"
            f"Generate a rigorous multiple-choice diagnostic practice problem. "
            f"Craft distractors that directly catch common misconceptions so we can pinpoint errors accurately."
        )

        system = (
            "You are a master psychometrician and STEM educator creating diagnostic test items. "
            "Every question must have exactly one logically sound correct answer, and distractors based on genuine student traps."
        )

        try:
            question: PracticeQuestion = await ollama_client.structured_output(
                prompt=prompt,
                schema_class=PracticeQuestion,
                system=system,
                temperature=0.2
            )
            return question
        except Exception as e:
            logger.error("Failed to generate practice question: %s", str(e))
            return PracticeQuestion(
                concept_name=concept_name,
                question_text=f"Explain the primary mechanism or definition of {concept_name}.",
                options=[
                    f"Correct standard definition of {concept_name}",
                    f"Common intuitive misconception regarding {concept_name}",
                    f"Unrelated physical/computational principle",
                    f"Opposite inverse relationship"
                ],
                correct_option_index=0,
                explanation=f"{concept_name} fundamentally describes the primary behavior.",
                hints=[f"Think about the foundational prerequisites of {concept_name}."]
            )

    async def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        correct_answer: str,
        concept_name: str
    ) -> AssessmentEvaluation:
        prompt = (
            f"Question: \"{question}\"\n"
            f"Correct Answer / Rubric: \"{correct_answer}\"\n"
            f"Student Answer: \"{student_answer}\"\n"
            f"Target Concept: \"{concept_name}\"\n\n"
            f"Evaluate the student's answer. Determine if it is conceptually sound, diagnose any misconception, "
            f"and provide helpful encouraging feedback."
        )

        system = (
            "You are a supportive, constructive AI teacher grading a student's answer. "
            "Identify conceptual strengths and precisely pinpoint misunderstandings."
        )

        try:
            eval_result: AssessmentEvaluation = await ollama_client.structured_output(
                prompt=prompt,
                schema_class=AssessmentEvaluation,
                system=system,
                temperature=0.1
            )
            return eval_result
        except Exception as e:
            logger.error("Answer evaluation failed: %s", str(e))
            is_match = student_answer.strip().lower() in correct_answer.strip().lower()
            return AssessmentEvaluation(
                is_correct=is_match,
                score=1.0 if is_match else 0.0,
                feedback="Good attempt. Review the core definition." if is_match else "Not quite correct. Let's revisit this step.",
                identified_misconception=None,
                recommended_remedy=f"Review {concept_name} fundamentals."
            )

assessment_engine = AssessmentEngine()
