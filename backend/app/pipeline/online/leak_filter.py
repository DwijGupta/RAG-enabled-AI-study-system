import re
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate prompt leakages or internal tags
LEAK_PATTERNS = [
    r'=== PEDAGOGICAL PLAN ===.*?(?=\n\n|$)',
    r'=== DIAGNOSTIC CONTEXT ===.*?(?=\n\n|$)',
    r'=== CITEABLE EVIDENCE ===.*?(?=\n\n|$)',
    r'=== STUDENT QUERY ===.*?(?=\n\n|$)',
    r'\[INTERNAL_.*?\]',
    r'Directive:\s*.*?(?=\n|$)',
    r'Action:\s*(EXPLAIN|SOCRATIC|HINT|REMEDIATE|QUIZ)\s*',
    r'```json[\s\S]*?```',
    r'P\(L_t\)',
]

class LeakFilter:
    """
    Step 12: Strips internal prompts, traces, and private learner metadata
    so the student receives a clean, polished, and empathetic tutor reply.
    """
    def sanitize(self, raw_text: str) -> str:
        clean = raw_text
        for pattern in LEAK_PATTERNS:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE | re.DOTALL)

        # Clean trailing and multiple blank lines
        clean = re.sub(r'\n{3,}', '\n\n', clean).strip()

        # Format citations consistently: replace e.g. [REF-1] with nice citation badge
        clean = re.sub(r'\[REF-(\d+)\]', r'[Doc \1]', clean)

        return clean

leak_filter = LeakFilter()
