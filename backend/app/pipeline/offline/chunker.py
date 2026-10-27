import re
import asyncio
import logging
from typing import List, Dict, Any, Optional
from app.core.llm_client import llm_client

logger = logging.getLogger(__name__)

class ContextualChunker:
    """
    Splits text hierarchically into atomic contextual chunks
    and prepends an LLM-generated contextual line for superior dense retrieval.
    """
    def __init__(self, target_chunk_size: int = 400, overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def split_into_paragraphs(self, text: str) -> List[str]:
        # Split on double newline or section markers
        raw_paras = re.split(r'\n\s*\n', text)
        clean_paras = [p.strip() for p in raw_paras if p.strip()]
        return clean_paras

    def create_hierarchical_chunks(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups page content into cohesive atomic chunks with page citations.
        """
        all_chunks = []
        chunk_idx = 0

        for page in pages:
            page_num = page["page_number"]
            page_text = page["text"]
            if not page_text:
                continue

            paragraphs = self.split_into_paragraphs(page_text)
            current_buffer = []
            current_words = 0
            current_section = ""

            for p in paragraphs:
                # Detect heading
                if len(p) < 80 and (p.isupper() or p.startswith("#") or p.endswith(":")):
                    current_section = p.replace("#", "").strip()

                words = p.split()
                if current_words + len(words) > self.target_chunk_size and current_buffer:
                    chunk_text = "\n\n".join(current_buffer)
                    all_chunks.append({
                        "chunk_index": chunk_idx,
                        "page_number": page_num,
                        "section_title": current_section or f"Page {page_num}",
                        "content": chunk_text,
                        "token_count": len(chunk_text.split()),
                        "difficulty_score": self._estimate_difficulty(chunk_text)
                    })
                    chunk_idx += 1
                    # Keep overlap
                    current_buffer = [current_buffer[-1]] if len(current_buffer) > 1 else []
                    current_words = len(current_buffer[0].split()) if current_buffer else 0

                current_buffer.append(p)
                current_words += len(words)

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                all_chunks.append({
                    "chunk_index": chunk_idx,
                    "page_number": page_num,
                    "section_title": current_section or f"Page {page_num}",
                    "content": chunk_text,
                    "token_count": len(chunk_text.split()),
                    "difficulty_score": self._estimate_difficulty(chunk_text)
                })
                chunk_idx += 1

        return all_chunks

    async def add_context_lines(self, chunks: List[Dict[str, Any]], doc_title: str) -> List[Dict[str, Any]]:
        """
        Adds an LLM-generated contextual preface line concurrently with semaphore gating.
        """
        if not chunks:
            return chunks

        sem = asyncio.Semaphore(5)

        async def _enrich_chunk(c: Dict[str, Any]):
            snippet = c["content"][:300]
            section = c.get("section_title") or f"Page {c['page_number']}"
            fallback_line = f"Explains {section} from {doc_title}."
            prompt = (
                f"Document: {doc_title}\n"
                f"Section: {section}\n"
                f"Content excerpt: {snippet}\n\n"
                f"Provide a single brief sentence (under 18 words) giving the exact context of what this chunk explains."
            )
            async with sem:
                try:
                    line = await llm_client.generate(prompt=prompt, temperature=0.1)
                    clean_line = line.strip().replace('"', '').replace('\n', ' ')
                    c["contextual_line"] = clean_line or fallback_line
                except Exception:
                    c["contextual_line"] = fallback_line
            return c

        tasks = []
        for i, c in enumerate(chunks):
            if i < 15:
                tasks.append(_enrich_chunk(c))
            else:
                c["contextual_line"] = f"Discusses {c.get('section_title', '')} in {doc_title}."

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return chunks

    def _estimate_difficulty(self, text: str) -> float:
        """
        Heuristic difficulty estimator based on technical terminology,
        word length, and mathematical density.
        """
        words = text.split()
        if not words:
            return 0.5
        avg_len = sum(len(w) for w in words) / len(words)
        math_count = sum(1 for c in text if c in "+-*/=^√∑∫πθλ")
        
        score = 0.3 + (avg_len - 4.5) * 0.1 + (math_count / max(1, len(words))) * 2.0
        return max(0.1, min(0.95, round(score, 2)))

contextual_chunker = ContextualChunker()
