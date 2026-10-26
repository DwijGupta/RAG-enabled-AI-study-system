import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.db import init_db
from app.core.ollama_client import ollama_client
from app.core.graph_db import graph_store
from app.api.routers.chat import router as chat_router
from app.api.routers.ingestion import router as ingestion_router
from app.api.routers.graph import router as graph_router
from app.api.routers.learner import router as learner_router
from app.api.routers.assessment import router as assessment_router
from app.api.routers.review import router as review_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("StudyBuddyApp")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Learner-State-Aware RAG Educational Tutor Backend...")
    # Initialize DB schema
    await init_db()
    
    # Ensure default student user exists and sync existing chunks into BM25
    from app.core.db import AsyncSessionLocal
    from app.core.models import User
    from app.pipeline.offline.indexer import offline_indexer

    try:
        async with AsyncSessionLocal() as session:
            demo_user = await session.get(User, "student_1")
            if not demo_user:
                demo_user = User(id="student_1", name="Alex Rivera", email="alex@student.edu")
                session.add(demo_user)
                await session.commit()
            await offline_indexer.sync_all_from_db(session)
    except Exception as e:
        logger.warning("Startup database synchronization notice: %s", str(e))

    # Check AI Brain (Google Gemini) connection
    brain_status = await ollama_client.check_health()
    logger.info("AI Brain Status (Gemini): %s", brain_status)
    yield
    logger.info("Shutting down backend and releasing system resources...")
    try:
        from app.core.db import engine
        from app.core.vector_db import vector_store
        from app.core.telemetry import telemetry_manager

        graph_store.close()
        vector_store.close()
        telemetry_manager.flush()
        await engine.dispose()
        logger.info("Backend resources cleanly released.")
    except Exception as e:
        logger.warning("Error during graceful shutdown: %s", str(e))

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for page inspector
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include Routers
app.include_router(chat_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(learner_router, prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(review_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    brain_info = await ollama_client.check_health()
    return {
        "status": "healthy",
        "project": "AI Study Buddy System",
        "version": settings.VERSION,
        "brain": brain_info,
        "graph_nodes": graph_store.nx_graph.number_of_nodes(),
        "graph_edges": graph_store.nx_graph.number_of_edges(),
        "using_neo4j": graph_store.use_neo4j
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
