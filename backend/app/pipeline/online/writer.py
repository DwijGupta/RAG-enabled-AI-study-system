import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.core.llm_client import llm_client
from app.pipeline.online.planner import TutorPlan
from app.pipeline.online.context_builder import PedagogicalContext

logger = logging.getLogger(__name__)

class GroundedWriter:
    """
    Step 9: Generates level-matched educational explanations using Google Gemini
    (with offline fallback) with strict inline citation spans [REF-X: Page Y].
    """
    def _build_prompt(
        self,
        query: str,
        plan: TutorPlan,
        context: PedagogicalContext
    ) -> (str, str):
        # Format Evidence Chunks
        evidence_str = ""
        if context.citeable_evidence:
            for ev in context.citeable_evidence:
                evidence_str += (
                    f"[{ev.cite_id}] ({ev.doc_title}, Page {ev.page_number}, Section: {ev.section_title}):\n"
                    f"{ev.content}\n\n"
                )
        else:
            evidence_str = "No specific textbook chunk retrieved. Base answer on established academic principles."

        # Diagnostic background
        diag_str = ""
        if context.prerequisite_context:
            diag_str += f"- {context.prerequisite_context}\n"
        if context.active_misconceptions:
            diag_str += f"- Known Misconception to address: {'; '.join(context.active_misconceptions)}\n"

        # Global Structural Context from GraphRAG Community Summaries
        macro_str = ""
        if getattr(context, "community_summaries", None):
            for comm in context.community_summaries[:2]:
                macro_str += f"- {comm.get('title', 'Community')}: {comm.get('summary', '')}\n"

        system_prompt = (
            "You are an inspiring, intellectually rigorous, and patient AI Study Buddy and Educational Tutor. "
            "Your explanations are crystal clear, encouraging, and strictly grounded in the provided evidence.\n\n"
            "MANDATORY CITATION RULES:\n"
            "1. Whenever you state a technical fact, theorem, formula, or quote, you MUST cite the source using the exact format: [REF-X: p. Y].\n"
            "2. Never fabricate citations or claim facts not supported by the evidence.\n"
            "3. Adapt your explanation strictly to the pedagogical plan directive below."
        )

        user_prompt = (
            f"=== PEDAGOGICAL PLAN ===\n"
            f"Action: {plan.action}\n"
            f"Directive: {plan.scaffolding_directive}\n"
            f"Student Mastery Level: {context.learner_mastery_level:.0%}\n\n"
            f"=== CURRICULUM MACRO CONTEXT (GRAPH COMMUNITY) ===\n"
            f"{macro_str or 'None'}\n\n"
            f"=== DIAGNOSTIC CONTEXT ===\n"
            f"{diag_str or 'None'}\n"
            f"=== CITEABLE EVIDENCE ===\n"
            f"{evidence_str}\n"
            f"=== STUDENT QUERY ===\n"
            f"\"{query}\"\n\n"
            f"Respond directly to the student adhering strictly to the Pedagogical Plan and Citation Rules."
        )

        return system_prompt, user_prompt

    async def write_answer(
        self,
        query: str,
        plan: TutorPlan,
        context: PedagogicalContext
    ) -> str:
        system_p, user_p = self._build_prompt(query, plan, context)
        response = await llm_client.generate(
            prompt=user_p,
            system=system_p,
            temperature=0.3
        )
        return response

    async def write_stream(
        self,
        query: str,
        plan: TutorPlan,
        context: PedagogicalContext
    ) -> AsyncGenerator[str, None]:
        system_p, user_p = self._build_prompt(query, plan, context)
        messages = [{"role": "user", "content": user_p}]
        async for chunk in llm_client.chat_stream(
            messages=messages,
            system=system_p,
            temperature=0.3
        ):
            yield chunk

grounded_writer = GroundedWriter()
