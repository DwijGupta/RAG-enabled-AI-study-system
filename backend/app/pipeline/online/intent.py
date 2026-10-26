import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class StudentIntent(BaseModel):
    question_type: str = Field(
        description="Type of query: 'conceptual_question', 'problem_solving', 'clarification', 'quiz_request', 'hint_request', or 'general'"
    )
    target_concepts: List[str] = Field(
        description="Key academic concepts involved in the query (e.g. ['Backpropagation', 'Gradient Descent'])"
    )
    learning_goal: str = Field(
        description="What the student wants to understand or accomplish."
    )
    suspected_misconception: Optional[str] = Field(
        default=None,
        description="Any specific misunderstanding or false assumption apparent in the student's question."
    )
    complexity_level: float = Field(
        default=0.5,
        description="Estimated question depth/difficulty (0.1 beginner to 1.0 advanced)."
    )

class IntentAnalyzer:
    async def analyze(self, user_query: str, recent_turns: Optional[List[dict]] = None) -> StudentIntent:
        """
        Step 1: Analyzes student input using Qwen 2.5 structured output.
        """
        context_str = ""
        if recent_turns:
            history = "\n".join([f"{t.get('role', 'user')}: {t.get('content', '')}" for t in recent_turns[-3:]])
            context_str = f"Recent conversation context:\n{history}\n\n"

        prompt = (
            f"{context_str}"
            f"Student Query: \"{user_query}\"\n\n"
            f"Analyze the student's cognitive intent, target concepts, learning goal, and whether they exhibit a misconception."
        )

        system = (
            "You are an expert pedagogical analyst. Classify student questions precisely, identify academic target concepts, "
            "and detect subtle misconceptions or false intuitions."
        )

        try:
            intent = await ollama_client.structured_output(
                prompt=prompt,
                schema_class=StudentIntent,
                system=system,
                temperature=0.1
            )
            return intent
        except Exception as e:
            logger.warning("Intent analysis structured output failed: %s. Using heuristics.", str(e))
            words = user_query.split()
            return StudentIntent(
                question_type="conceptual_question",
                target_concepts=[w for w in words if len(w) > 4][:2],
                learning_goal=user_query,
                suspected_misconception=None,
                complexity_level=0.5
            )

intent_analyzer = IntentAnalyzer()
