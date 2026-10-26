import logging
from typing import Optional, Tuple
from app.core.ollama_client import ollama_client

logger = logging.getLogger(__name__)

class FallbackLoop:
    """
    Step 11: Verification fallback loop.
    Triggers query reformulation, broadened retrieval, or clarifying response.
    """
    async def rewrite_query(self, original_query: str, failed_concepts: Optional[str] = None) -> str:
        prompt = (
            f"Original Student Query: \"{original_query}\"\n"
            f"Failed / Missing Concept Context: {failed_concepts or 'General'}\n\n"
            f"Rewrite this query into 2-3 focused academic search keywords to retrieve authoritative textbook explanations."
        )
        try:
            rewritten = await ollama_client.generate(prompt=prompt, temperature=0.2)
            clean = rewritten.strip().replace('"', '').replace('\n', ' ')
            logger.info("Rewrote query: '%s' -> '%s'", original_query, clean)
            return clean
        except Exception as e:
            logger.warning("Query rewrite failed: %s", str(e))
            return original_query

    def create_clarification_response(self, query: str, missing_concept: Optional[str] = None) -> str:
        if missing_concept:
            return (
                f"To give you the most accurate explanation regarding **{missing_concept}**, "
                f"could you clarify which specific aspect you're working on, or would you like to review "
                f"the foundational definition first?"
            )
        return (
            f"I want to make sure I answer your question accurately without guessing. "
            f"Could you share a bit more context or the specific problem you're trying to solve?"
        )

fallback_loop = FallbackLoop()
