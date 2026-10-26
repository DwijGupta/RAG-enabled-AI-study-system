import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.pipeline.online.intent import StudentIntent
from app.pipeline.online.context_builder import PedagogicalContext

logger = logging.getLogger(__name__)

class TutorPlan(BaseModel):
    action: str = Field(
        description="Pedagogical action: 'EXPLAIN', 'SOCRATIC', 'HINT', 'REMEDIATE', 'WORKED_EXAMPLE', or 'QUIZ'"
    )
    rationale: str = Field(
        description="Reasoning behind choosing this action based on learner state and ZPD."
    )
    scaffolding_directive: str = Field(
        description="Direct instruction for the writer model on tone, depth, and pedagogical technique."
    )

class TutorPlanner:
    """
    Step 8: Pedagogical planner combining rule guardrails and cognitive policy
    to select the optimal learning strategy.
    """
    def plan(
        self,
        intent: StudentIntent,
        context: PedagogicalContext,
        root_cause_result: Dict[str, Any]
    ) -> TutorPlan:
        q_type = intent.question_type.lower()
        mastery = context.learner_mastery_level
        has_root_gap = root_cause_result.get("has_weakness", False)
        weak_node = root_cause_result.get("weakest_concept")
        is_direct = root_cause_result.get("is_direct_target", True)

        # Rule Guardrail 1: Explicit Quiz Request
        if "quiz" in q_type:
            return TutorPlan(
                action="QUIZ",
                rationale="Student explicitly requested an assessment.",
                scaffolding_directive="Generate a diagnostic practice problem with 4 options or open response testing their understanding."
            )

        # Rule Guardrail 2: Explicit Hint Request
        if "hint" in q_type:
            return TutorPlan(
                action="HINT",
                rationale="Student is stuck and requested a nudge.",
                scaffolding_directive="Provide a subtle hint or guiding step without revealing the full answer."
            )

        # Rule Guardrail 3: Upstream Prerequisite Gap (Remediate)
        if has_root_gap and not is_direct and mastery < 0.45:
            return TutorPlan(
                action="REMEDIATE",
                rationale=f"Student is asking an advanced question, but lacks foundational prerequisite: '{weak_node}'.",
                scaffolding_directive=(
                    f"First gently introduce or refresh the prerequisite concept '{weak_node}' using an intuitive analogy, "
                    f"then connect it back to answer their primary question."
                )
            )

        # Rule Guardrail 4: Active Misconception Detected
        if context.active_misconceptions:
            misconception_info = context.active_misconceptions[0]
            return TutorPlan(
                action="REMEDIATE",
                rationale="A known cognitive misconception is active.",
                scaffolding_directive=(
                    f"Directly and compassionately address the misconception ({misconception_info}). "
                    f"Provide a clear counter-example from the evidence to show why the intuitive belief fails."
                )
            )

        # Rule Guardrail 5: In ZPD (Zone of Proximal Development: 0.50 - 0.75)
        if 0.50 <= mastery <= 0.75 and q_type in ["problem_solving", "clarification"]:
            return TutorPlan(
                action="SOCRATIC",
                rationale="Student is within ZPD. Socratic guidance stimulates active recall and cognitive scaffolding.",
                scaffolding_directive=(
                    "Do not just hand out the complete solution. Explain the first conceptual principle, "
                    "then ask a thought-provoking guiding question to let the student solve the next step."
                )
            )

        # Default Rule: Grounded Explanation
        return TutorPlan(
            action="EXPLAIN",
            rationale="Introducing or clarifying concept with full grounded explanation.",
            scaffolding_directive=(
                "Provide a clear, engaging, and step-by-step grounded explanation. "
                "Include a concrete real-world example and strictly cite all source evidence."
            )
        )

tutor_planner = TutorPlanner()
