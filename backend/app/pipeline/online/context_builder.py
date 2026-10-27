import logging
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class CiteableEvidence(BaseModel):
    cite_id: str
    doc_title: str
    page_number: int
    section_title: str
    content: str
    image_url: Optional[str] = None

    def to_xml_tag(self) -> str:
        """Structured XML grounding format optimized for native Gemini comprehension."""
        return (
            f'<source id="{self.cite_id}" doc="{self.doc_title}" page="{self.page_number}">\n'
            f'{self.content.strip()}\n'
            f'</source>'
        )

class PedagogicalContext(BaseModel):
    citeable_evidence: List[CiteableEvidence] = Field(default_factory=list)
    prerequisite_context: Optional[str] = None
    diagnosed_weakness: Optional[str] = None
    active_misconceptions: List[str] = Field(default_factory=list)
    learner_mastery_level: float = 0.5
    recent_history: List[Dict[str, str]] = Field(default_factory=list)
    past_traces: List[str] = Field(default_factory=list)
    community_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    token_budget: int = 5000

class ContextBuilder:
    """
    Step 7: Builds a typed, token-budgeted, deduplicated pedagogical context.
    Prunes redundant overlap between vector chunks and graph communities,
    and structures evidence for native XML-based Gemini grounding.
    """
    def _is_redundant(self, text: str, seen_snippets: List[str], threshold: float = 0.82) -> bool:
        """Fast Jaccard-based snippet overlap checker to eliminate duplicate chunk boundaries."""
        words_new = set(text.lower().split())
        if not words_new:
            return True
        for prev in seen_snippets:
            words_prev = set(prev.lower().split())
            intersection = len(words_new.intersection(words_prev))
            union = len(words_new.union(words_prev))
            if union > 0 and (intersection / union) > threshold:
                return True
        return False

    def build_context(
        self,
        reranked_chunks: List[Dict[str, Any]],
        root_cause_result: Dict[str, Any],
        learner_mastery: float,
        session_turns: List[Dict[str, str]],
        past_traces: List[Dict[str, Any]],
        community_summaries: Optional[List[Dict[str, Any]]] = None,
        token_budget: int = 5000
    ) -> PedagogicalContext:
        evidence_items: List[CiteableEvidence] = []
        seen_snippets: List[str] = []
        consumed_tokens = 0

        # 1. Prune and select top diverse chunks
        for i, c in enumerate(reranked_chunks):
            content = c.get("content", "").strip()
            if not content:
                continue

            # Deduplicate chunk overlap
            if self._is_redundant(content, seen_snippets):
                continue

            chunk_tokens = int(len(content.split()) * 1.3)
            if consumed_tokens + chunk_tokens > token_budget:
                break

            doc_title = c.get("doc_title", "Course Material")
            page_num = c.get("page_number", 1)
            cite_id = f"REF-{len(evidence_items) + 1}"

            evidence_items.append(CiteableEvidence(
                cite_id=cite_id,
                doc_title=doc_title,
                page_number=page_num,
                section_title=c.get("section_title", f"Page {page_num}"),
                content=content,
                image_url=f"/storage/pages/{c.get('doc_id')}_page_{page_num}.png"
            ))
            seen_snippets.append(content[:150])
            consumed_tokens += chunk_tokens

        # 2. Prune Graph Communities to only those not already saturated by retrieved chunks
        pruned_communities = []
        if community_summaries:
            for comm in community_summaries[:2]:
                summary_text = comm.get("summary", "")
                if not self._is_redundant(summary_text, seen_snippets):
                    pruned_communities.append(comm)

        # 3. Format prerequisite diagnostic notes
        prereq_note = None
        misconception_list = []
        if root_cause_result.get("has_weakness"):
            weak_c = root_cause_result.get("weakest_concept")
            m_score = root_cause_result.get("mastery_score", 0.0)
            prereq_note = (
                f"Prerequisite Gap: Student lacks foundation in '{weak_c}' "
                f"(current mastery: {m_score:.0%})."
            )
            for m in root_cause_result.get("active_misconceptions", []):
                misconception_list.append(f"{m.get('name')}: {m.get('description')}")

        trace_summaries = []
        for t in past_traces:
            payload = t.get("payload", {})
            q = payload.get("query")
            w = payload.get("weak_concept")
            if q:
                trace_summaries.append(f"Previously asked: '{q}' (Target: {w or 'General'})")

        return PedagogicalContext(
            citeable_evidence=evidence_items,
            prerequisite_context=prereq_note,
            diagnosed_weakness=root_cause_result.get("weakest_concept"),
            active_misconceptions=misconception_list,
            learner_mastery_level=learner_mastery,
            recent_history=session_turns[-3:],
            past_traces=trace_summaries[:2],
            community_summaries=pruned_communities,
            token_budget=token_budget
        )

context_builder = ContextBuilder()
