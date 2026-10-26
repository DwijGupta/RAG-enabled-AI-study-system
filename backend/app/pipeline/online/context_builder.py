import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CiteableEvidence(BaseModel):
    cite_id: str
    doc_title: str
    page_number: int
    section_title: str
    content: str
    image_url: Optional[str] = None

class PedagogicalContext(BaseModel):
    citeable_evidence: List[CiteableEvidence] = Field(default_factory=list)
    prerequisite_context: Optional[str] = None
    diagnosed_weakness: Optional[str] = None
    active_misconceptions: List[str] = Field(default_factory=list)
    learner_mastery_level: float = 0.5
    recent_history: List[Dict[str, str]] = Field(default_factory=list)
    past_traces: List[str] = Field(default_factory=list)
    community_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    token_budget: int = 3500

class ContextBuilder:
    """
    Step 7: Builds a typed, token-budgeted pedagogical context
    combining citeable evidence, cognitive diagnoses, and learner state.
    """
    def build_context(
        self,
        reranked_chunks: List[Dict[str, Any]],
        root_cause_result: Dict[str, Any],
        learner_mastery: float,
        session_turns: List[Dict[str, str]],
        past_traces: List[Dict[str, Any]],
        community_summaries: Optional[List[Dict[str, Any]]] = None,
        token_budget: int = 3500
    ) -> PedagogicalContext:
        evidence_items = []
        consumed_tokens = 0

        for i, c in enumerate(reranked_chunks):
            cite_id = f"REF-{i+1}"
            doc_title = c.get("doc_title", "Textbook")
            page_num = c.get("page_number", 1)
            content = c.get("content", "").strip()
            
            # Simple token estimate (1 word ~= 1.3 tokens)
            chunk_tokens = int(len(content.split()) * 1.3)
            if consumed_tokens + chunk_tokens > token_budget:
                break

            evidence_items.append(CiteableEvidence(
                cite_id=cite_id,
                doc_title=doc_title,
                page_number=page_num,
                section_title=c.get("section_title", f"Page {page_num}"),
                content=content,
                image_url=f"/storage/pages/{c.get('doc_id')}_page_{page_num}.png"
            ))
            consumed_tokens += chunk_tokens

        # Format prerequisite diagnostic notes
        prereq_note = None
        misconception_list = []
        if root_cause_result.get("has_weakness"):
            weak_c = root_cause_result.get("weakest_concept")
            m_score = root_cause_result.get("mastery_score", 0.0)
            prereq_note = (
                f"Cognitive Diagnosis: The student has a prerequisite gap in foundational concept '{weak_c}' "
                f"(Current Mastery: {m_score:.0%})."
            )
            for m in root_cause_result.get("active_misconceptions", []):
                misconception_list.append(f"{m.get('name')}: {m.get('description')}")

        trace_summaries = []
        for t in past_traces:
            payload = t.get("payload", {})
            q = payload.get("query")
            w = payload.get("weak_concept")
            if q:
                trace_summaries.append(f"Previously asked: '{q}' (Struggled with: {w or 'General'})")

        return PedagogicalContext(
            citeable_evidence=evidence_items,
            prerequisite_context=prereq_note,
            diagnosed_weakness=root_cause_result.get("weakest_concept"),
            active_misconceptions=misconception_list,
            learner_mastery_level=learner_mastery,
            recent_history=session_turns[-4:],
            past_traces=trace_summaries,
            community_summaries=community_summaries or [],
            token_budget=token_budget
        )

context_builder = ContextBuilder()

