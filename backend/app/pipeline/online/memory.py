import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.models import InteractionTrace
from app.core.embeddings import embedding_service
from app.core.vector_db import vector_store

logger = logging.getLogger(__name__)

# Fast in-memory session store (with Redis-compatible API)
_ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

class MemoryManager:
    """
    Step 3: Manages multi-turn session memory, active subtopics,
    and searchable episodic past-session traces in Qdrant.
    """
    def get_or_create_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        if session_id not in _ACTIVE_SESSIONS:
            _ACTIVE_SESSIONS[session_id] = {
                "session_id": session_id,
                "user_id": user_id,
                "turns": [],
                "active_subtopic": None,
                "unresolved_questions": [],
                "diagnosed_weaknesses": []
            }
        return _ACTIVE_SESSIONS[session_id]

    def add_turn(self, session_id: str, user_id: str, role: str, content: str):
        session = self.get_or_create_session(session_id, user_id)
        session["turns"].append({"role": role, "content": content})
        # Keep last 10 turns in active context
        if len(session["turns"]) > 10:
            session["turns"] = session["turns"][-10:]

    def set_active_subtopic(self, session_id: str, user_id: str, subtopic: str):
        session = self.get_or_create_session(session_id, user_id)
        session["active_subtopic"] = subtopic

    def add_unresolved(self, session_id: str, user_id: str, question: str):
        session = self.get_or_create_session(session_id, user_id)
        if question not in session["unresolved_questions"]:
            session["unresolved_questions"].append(question)

    def resolve_question(self, session_id: str, user_id: str, question: str):
        session = self.get_or_create_session(session_id, user_id)
        if question in session["unresolved_questions"]:
            session["unresolved_questions"].remove(question)

    async def retrieve_past_traces(self, user_id: str, current_query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Searches Qdrant vector store for past interaction traces
        where student asked about similar concepts or encountered misconceptions.
        """
        query_vec = embedding_service.embed_query(current_query)
        traces = vector_store.search_traces(user_id=user_id, query_vector=query_vec, limit=limit)
        return traces

    async def log_interaction_trace(
        self,
        user_id: str,
        session_id: str,
        user_query: str,
        tutor_response: str,
        intent_type: str,
        target_concepts: List[str],
        diagnosed_weak_concept: Optional[str],
        planner_action: str,
        citations: List[Dict[str, Any]],
        faithfulness_score: float,
        db: AsyncSession
    ) -> str:
        """
        Persists episodic trace to PostgreSQL/SQLite AND indexes it into Qdrant vectors.
        """
        trace = InteractionTrace(
            user_id=user_id,
            session_id=session_id,
            user_query=user_query,
            tutor_response=tutor_response,
            intent_type=intent_type,
            target_concepts=target_concepts,
            diagnosed_weak_concept=diagnosed_weak_concept,
            planner_action=planner_action,
            citations=citations,
            faithfulness_score=faithfulness_score
        )
        db.add(trace)
        await db.commit()
        await db.refresh(trace)

        # Vectorize trace for future retrieval
        trace_text = f"Student asked: {user_query}\nTarget concepts: {', '.join(target_concepts)}\nWeakness: {diagnosed_weak_concept or 'None'}"
        trace_vec = embedding_service.embed_query(trace_text)
        
        vector_store.upsert_trace(
            trace_id=trace.id,
            vector=trace_vec,
            payload={
                "trace_id": trace.id,
                "user_id": user_id,
                "session_id": session_id,
                "query": user_query,
                "weak_concept": diagnosed_weak_concept,
                "planner_action": planner_action,
                "timestamp": str(trace.created_at)
            }
        )

        return trace.id

memory_manager = MemoryManager()
