import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, AsyncSessionLocal
from app.pipeline.online.coordinator import online_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat & Streaming Tutor"])

class ChatRequest(BaseModel):
    user_id: str = "student_1"
    session_id: str = "session_default"
    query: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    intent: Dict[str, Any]
    planner_action: str
    rationale: str
    learner_mastery: float
    diagnosed_weakness: Optional[str] = None
    faithfulness_score: float
    latency_ms: float
    trace_id: Optional[str] = None


from sqlalchemy import select, delete, desc
from app.core.models import InteractionTrace, User
from app.pipeline.online.memory import _ACTIVE_SESSIONS

@router.post("/message", response_model=ChatResponse)
async def chat_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Ensure user exists to satisfy foreign key constraint
    user = await db.get(User, req.user_id)
    if not user:
        user = User(id=req.user_id, name="Student")
        db.add(user)
        await db.commit()

    result = await online_pipeline.run(
        user_id=req.user_id,
        session_id=req.session_id,
        user_query=req.query,
        db=db
    )
    return ChatResponse(**result)

@router.get("/sessions")
async def get_chat_sessions(user_id: str = "student_1", db: AsyncSession = Depends(get_db)):
    """
    Returns list of past and active chat sessions for the student so memory can be seen back.
    """
    res = await db.execute(
        select(InteractionTrace)
        .where(InteractionTrace.user_id == user_id)
        .order_by(InteractionTrace.created_at.desc())
    )
    traces = res.scalars().all()
    sessions_map: Dict[str, Dict[str, Any]] = {}
    
    for t in traces:
        sid = t.session_id
        if sid not in sessions_map:
            sessions_map[sid] = {
                "session_id": sid,
                "title": t.user_query[:50] + ("..." if len(t.user_query) > 50 else ""),
                "last_query": t.user_query,
                "last_active": t.created_at.strftime("%b %d, %H:%M") if t.created_at else "Recently",
                "turns_count": 0,
                "target_concepts": t.target_concepts or []
            }
        sessions_map[sid]["turns_count"] += 1

    # Include in-memory active sessions if any
    for sid, sdata in _ACTIVE_SESSIONS.items():
        if sdata.get("user_id") == user_id and sid not in sessions_map:
            turns = sdata.get("turns", [])
            first_user_q = next((turn["content"] for turn in turns if turn.get("role") == "user"), "Active Session")
            sessions_map[sid] = {
                "session_id": sid,
                "title": first_user_q[:50],
                "last_query": first_user_q,
                "last_active": "Just now",
                "turns_count": max(1, len(turns) // 2),
                "target_concepts": []
            }

    return list(sessions_map.values())

@router.get("/history/{session_id}")
async def get_session_history(session_id: str, user_id: str = "student_1", db: AsyncSession = Depends(get_db)):
    """
    Reconstructs the full multi-turn conversation and citations for a past session so student can see it back.
    """
    res = await db.execute(
        select(InteractionTrace)
        .where(InteractionTrace.session_id == session_id)
        .order_by(InteractionTrace.created_at.asc())
    )
    traces = res.scalars().all()
    messages = []
    for t in traces:
        ts = t.created_at.strftime("%I:%M %p") if t.created_at else "Just now"
        # 1. User message
        messages.append({
            "id": f"msg-user-{t.id}",
            "trace_id": t.id,
            "sender": "user",
            "timestamp": ts,
            "content": t.user_query
        })
        # 2. Tutor response
        messages.append({
            "id": f"msg-tutor-{t.id}",
            "trace_id": t.id,
            "sender": "tutor",
            "timestamp": ts,
            "content": t.tutor_response,
            "citations": t.citations or [],
            "mode": t.planner_action or "Learn",
            "faithfulness": t.faithfulness_score or 1.0,
            "weakness": t.diagnosed_weak_concept
        })
    return {
        "session_id": session_id,
        "messages": messages,
        "turns_count": len(traces)
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes all interaction traces and chat memory for a given session.
    """
    await db.execute(delete(InteractionTrace).where(InteractionTrace.session_id == session_id))
    await db.commit()
    if session_id in _ACTIVE_SESSIONS:
        del _ACTIVE_SESSIONS[session_id]
    logger.info("Deleted session %s and cleared its memory.", session_id)
    return {"status": "success", "deleted_session_id": session_id}

@router.delete("/message/{trace_id}")
async def delete_message(trace_id: str, db: AsyncSession = Depends(get_db)):
    """
    Deletes a single message/turn from interaction traces.
    """
    await db.execute(delete(InteractionTrace).where(InteractionTrace.id == trace_id))
    await db.commit()
    return {"status": "success", "deleted_trace_id": trace_id}


@router.websocket("/ws/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info("WebSocket connected for session: %s", session_id)
    try:
        while True:
            data_text = await websocket.receive_text()
            data = json.loads(data_text)
            user_id = data.get("user_id", "student_1")
            query = data.get("query", "")

            if not query.strip():
                continue

            # Notify UI that processing has begun
            await websocket.send_json({"type": "status", "stage": "analyzing_intent"})

            async with AsyncSessionLocal() as db:
                result = await online_pipeline.run(
                    user_id=user_id,
                    session_id=session_id,
                    user_query=query,
                    db=db
                )

            # Send complete validated result
            await websocket.send_json({
                "type": "tutor_response",
                "payload": result
            })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session: %s", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
        await websocket.close()
