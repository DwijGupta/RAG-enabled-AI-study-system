import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.core.llm_client import llm_client
from app.pipeline.online.planner import TutorPlan
from app.pipeline.online.context_builder import PedagogicalContext

logger = logging.getLogger(__name__)

class GroundedWriter:
    """
    Step 9: Generates level-matched educational explanations using Google Gemini.
    Embeds pedagogical scaffolding and cognitive policy directly in System Instructions,
    and structures evidence as native XML <source> tags for optimal grounding and citation accuracy.
    """
    def _build_prompt(
        self,
        query: str,
        plan: TutorPlan,
        context: PedagogicalContext
    ) -> (str, str):
        mastery = context.learner_mastery_level

        # 1. Determine Dynamic Pedagogical Stance for System Instructions
        if mastery < 0.45:
            pedagogical_stance = (
                f"The student is currently developing foundational comprehension (Mastery: {mastery:.0%}). "
                "Adopt a supportive scaffolding approach: break difficult ideas into digestible steps, "
                "use vivid real-world analogies, and connect foundational basics intuitively."
            )
        elif mastery >= 0.75:
            pedagogical_stance = (
                f"The student demonstrates advanced mastery (Mastery: {mastery:.0%}). "
                "Use a rigorous, intellectually stimulating tone: emphasize formal principles, "
                "subtle edge cases, and pose an open-ended Socratic question to stretch their thinking."
            )
        else:
            pedagogical_stance = (
                f"The student has intermediate familiarity (Mastery: {mastery:.0%}). "
                "Provide a balanced, structured explanation featuring clear definitions, "
                "concrete worked examples, and practical takeaways."
            )

        # Pedagogical Strategy Directive from TutorPlan
        strategy_directive = f"Strategy Directive: {plan.scaffolding_directive}"
        if context.prerequisite_context:
            strategy_directive += f"\n- {context.prerequisite_context}"
        if context.active_misconceptions:
            strategy_directive += f"\n- Pre-emptively clarify this common misconception: {'; '.join(context.active_misconceptions)}"

        # System Prompt
        system_prompt = (
            "You are an inspiring, intellectually rigorous, and patient AI Study Buddy and Educational Tutor.\n\n"
            "CORE PEDAGOGICAL PRINCIPLES:\n"
            f"1. {pedagogical_stance}\n"
            f"2. {strategy_directive}\n\n"
            "RESPONSE DEPTH & THOROUGHNESS REQUIREMENTS:\n"
            "1. Deliver an extensive, deeply explanatory response (at least 3 to 5 substantial, well-developed paragraphs).\n"
            "2. Thoroughly unpack the mathematical foundations, core definitions, and intuitive physical/practical analogies.\n"
            "3. Do not cut answers short or deliver superficial summaries unless the student explicitly requests brevity.\n"
            "4. Structure your answer with clear markdown subheadings, bold terminology, and LaTeX formulas ($$ ... $$) where relevant.\n\n"
            "CITATION & GROUNDING RULES:\n"
            "1. Ground all technical assertions strictly in the provided <source> documents.\n"
            "2. Whenever citing facts, theorems, formulas, or concepts from a source, use the exact format: [REF-X: p. Y] "
            "(e.g., [REF-1: p. 4]).\n"
            "3. If a question cannot be answered from the sources, state what is known from the sources and note the limitation.\n"
            "4. Maintain an engaging, lucid, academic tutor voice."
        )

        # 2. Format XML Evidence Tags
        if context.citeable_evidence:
            xml_sources = "\n".join([ev.to_xml_tag() for ev in context.citeable_evidence])
        else:
            xml_sources = "<source id=\"GENERAL\" doc=\"Academic Knowledge\" page=\"1\">\nGeneral foundational curriculum principles.\n</source>"

        # Macro-Curriculum Communities Context
        community_section = ""
        if context.community_summaries:
            comm_lines = [f"- {c.get('title', 'Community')}: {c.get('summary', '')}" for c in context.community_summaries]
            community_section = f"\n<curriculum_context>\n{chr(10).join(comm_lines)}\n</curriculum_context>\n"

        user_prompt = (
            f"<sources>\n{xml_sources}\n</sources>{community_section}\n\n"
            f"Student Question: \"{query}\"\n\n"
            "Please provide a comprehensive, clear, and citation-grounded response to help the student learn effectively."
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
