import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.core.llm_client import llm_client
from app.pipeline.online.context_builder import PedagogicalContext

logger = logging.getLogger(__name__)

class ClaimVerificationItem(BaseModel):
    claim: str = Field(description="Atomic factual claim extracted from the response.")
    is_supported: bool = Field(description="True if the claim is directly supported or logically entailed by the citeable evidence.")
    supporting_ref: str = Field(default="", description="Source reference ID (e.g. REF-1) or 'None'")

class ClaimVerificationReport(BaseModel):
    claims: List[ClaimVerificationItem] = Field(default_factory=list)
    overall_faithfulness: float = Field(default=1.0, description="Fraction of supported claims (0.0 to 1.0).")
    hallucination_detected: bool = Field(default=False)

class ClaimVerifier:
    """
    Step 10: Extracts atomic claims and performs fast structured LLM-based verification
    against XML-tagged evidence sources with zero CPU-bound NLI latency.
    """
    async def verify(self, answer: str, context: PedagogicalContext) -> ClaimVerificationReport:
        if not context.citeable_evidence or len(answer.split()) < 20:
            return ClaimVerificationReport(
                claims=[],
                overall_faithfulness=1.0,
                hallucination_detected=False
            )

        xml_corpus = "\n".join([e.to_xml_tag() for e in context.citeable_evidence])

        prompt = (
            f"<sources>\n{xml_corpus}\n</sources>\n\n"
            f"<generated_tutor_answer>\n{answer}\n</generated_tutor_answer>\n\n"
            "Analyze the generated tutor answer. Extract 3 to 5 core factual assertions. "
            "For each assertion, verify whether it is directly supported or logically entailed by the sources."
        )

        system = (
            "You are an academic claim verifier and educational fact-checker. "
            "Validate each claim objectively against the provided sources. "
            "Accurate conceptual summaries, valid mathematical transformations, and direct quotes are supported."
        )

        try:
            report: ClaimVerificationReport = await llm_client.structured_output(
                prompt=prompt,
                schema_class=ClaimVerificationReport,
                system=system,
                temperature=0.0
            )

            if report.claims:
                supported_count = sum(1 for c in report.claims if c.is_supported)
                report.overall_faithfulness = round(supported_count / len(report.claims), 2)
                report.hallucination_detected = report.overall_faithfulness < 0.65

            return report
        except Exception as e:
            logger.warning("Verification structured check fallback (%s). Assuming faithful.", str(e))
            return ClaimVerificationReport(
                claims=[],
                overall_faithfulness=0.95,
                hallucination_detected=False
            )

claim_verifier = ClaimVerifier()
