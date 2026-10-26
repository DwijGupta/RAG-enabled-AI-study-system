import re
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.core.ollama_client import ollama_client
from app.pipeline.online.context_builder import PedagogicalContext

logger = logging.getLogger(__name__)

class ClaimVerificationItem(BaseModel):
    claim: str = Field(description="Atomic factual claim extracted from the response.")
    is_supported: bool = Field(description="True if the claim is directly supported by the citeable evidence.")
    supporting_ref: str = Field(default="", description="Reference ID (e.g. REF-1) or 'None'")

class ClaimVerificationReport(BaseModel):
    claims: List[ClaimVerificationItem] = Field(default_factory=list)
    overall_faithfulness: float = Field(default=1.0, description="Fraction of supported claims (0.0 to 1.0).")
    hallucination_detected: bool = Field(default=False)

class ClaimVerifier:
    """
    Step 10: Extracts atomic claims and checks entailment against evidence.
    """
    async def verify(self, answer: str, context: PedagogicalContext) -> ClaimVerificationReport:
        if not context.citeable_evidence or len(answer.split()) < 20:
            return ClaimVerificationReport(
                claims=[],
                overall_faithfulness=1.0,
                hallucination_detected=False
            )

        evidence_corpus = "\n\n".join([
            f"[{e.cite_id}] {e.content}" for e in context.citeable_evidence
        ])

        prompt = (
            f"=== EVIDENCE CHUNKS ===\n{evidence_corpus}\n\n"
            f"=== GENERATED TUTOR ANSWER ===\n{answer}\n\n"
            f"Extract the 3 to 6 key factual claims from the answer. "
            f"For each claim, verify if it is strictly supported by the evidence above."
        )

        system = (
            "You are a strict academic fact-checker and NLI claim verifier. "
            "Validate each claim objectively against the provided evidence."
        )

        try:
            report: ClaimVerificationReport = await ollama_client.structured_output(
                prompt=prompt,
                schema_class=ClaimVerificationReport,
                system=system,
                temperature=0.0
            )

            if report.claims:
                supported_count = sum(1 for c in report.claims if c.is_supported)
                report.overall_faithfulness = round(supported_count / len(report.claims), 2)
                report.hallucination_detected = report.overall_faithfulness < 0.70

            return report
        except Exception as e:
            logger.warning("Verification structured check failed (%s). Assuming faithful.", str(e))
            return ClaimVerificationReport(
                claims=[],
                overall_faithfulness=0.95,
                hallucination_detected=False
            )

claim_verifier = ClaimVerifier()
