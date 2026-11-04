import os
import time
import uuid
import shutil
import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db, AsyncSessionLocal
from app.core.models import Document, PageImage
from app.pipeline.offline.indexer import offline_indexer
from app.core.security import sanitize_filename, validate_safe_url, expensive_rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingestion", tags=["Document Ingestion"])

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".bmp": "image",
    ".gif": "image",
    ".docx": "docx",
    ".doc": "docx",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".txt": "note",
    ".md": "note",
    ".mp4": "video"
}

class IngestionJobManager:
    """Tracks background ingestion tasks, providing non-blocking real-time status."""
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, job_id: str, title: str, filename: str) -> Dict[str, Any]:
        now = time.time()
        job = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "stage": "Queued for processing...",
            "title": title,
            "filename": filename,
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now
        }
        self._jobs[job_id] = job
        return job

    def update_status(self, job_id: str, status: str, progress: int, stage: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            self._jobs[job_id]["progress"] = progress
            self._jobs[job_id]["stage"] = stage
            self._jobs[job_id]["updated_at"] = time.time()

    def complete_job(self, job_id: str, result: Dict[str, Any]):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "completed"
            self._jobs[job_id]["progress"] = 100
            self._jobs[job_id]["stage"] = "Knowledge base indexing complete!"
            self._jobs[job_id]["result"] = result
            self._jobs[job_id]["updated_at"] = time.time()

    def fail_job(self, job_id: str, error_msg: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["stage"] = f"Failed: {error_msg}"
            self._jobs[job_id]["error"] = error_msg
            self._jobs[job_id]["updated_at"] = time.time()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._jobs.get(job_id)

job_manager = IngestionJobManager()

async def _run_background_indexing(
    job_id: str,
    file_path: str,
    title: str,
    source_type: str,
    filename: str
):
    """Executes the heavy document ingestion pipeline in an isolated DB session."""
    logger.info("Starting background ingestion worker for job %s ('%s')", job_id, title)
    async with AsyncSessionLocal() as session:
        try:
            def _progress_cb(pct: int, msg: str):
                job_manager.update_status(job_id, "processing", progress=pct, stage=msg)

            result = await offline_indexer.index_source(
                file_path_or_content=file_path,
                title=title,
                source_type=source_type,
                db=session,
                original_filename=filename,
                progress_callback=_progress_cb
            )
            job_manager.complete_job(job_id, result)
            logger.info("Background ingestion completed successfully for job %s", job_id)
        except Exception as e:
            logger.error("Background ingestion failed for job %s: %s", job_id, str(e), exc_info=True)
            job_manager.fail_job(job_id, str(e))

@router.post("/upload", dependencies=[Depends(expensive_rate_limiter)])
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Non-blocking multi-format document and image ingestion endpoint.
    Includes anti-directory traversal filename sanitization and maximum file size enforcement.
    Immediately returns HTTP 202 Accepted with a job_id for client progress tracking.
    """
    clean_filename = sanitize_filename(file.filename)
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    detected_type = SUPPORTED_EXTENSIONS[ext]
    doc_title = title or clean_filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    
    uploads_dir = os.path.join(settings.STORAGE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = f"{os.urandom(8).hex()}_{clean_filename}"
    upload_path = os.path.join(uploads_dir, safe_name)

    # Save uploaded file payload with streaming chunk size-limit enforcement
    total_bytes = 0
    chunk_size = 1024 * 1024
    try:
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_bytes:
                    buffer.close()
                    if os.path.exists(upload_path):
                        os.remove(upload_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException(status_code=500, detail=f"Failed to save file payload: {str(e)}")

    job_id = str(uuid.uuid4())
    job_manager.create_job(job_id, title=doc_title, filename=clean_filename)
    logger.info("Queued %s (%s, %d bytes) with job_id %s -> %s", detected_type, clean_filename, total_bytes, job_id, upload_path)

    # Dispatch to background task worker to prevent thread blocking
    background_tasks.add_task(
        _run_background_indexing,
        job_id=job_id,
        file_path=upload_path,
        title=doc_title,
        source_type=detected_type,
        filename=clean_filename
    )

    return JSONResponse(
        status_code=202,
        content={
            "status": "queued",
            "job_id": job_id,
            "message": f"Document '{doc_title}' queued for processing.",
            "title": doc_title,
            "filename": clean_filename
        }
    )

@router.post("/upload-pdf", dependencies=[Depends(expensive_rate_limiter)])
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Backward compatibility alias for PDF upload."""
    return await upload_file(file=file, title=title, background_tasks=background_tasks)

@router.post("/import-url", dependencies=[Depends(expensive_rate_limiter)])
async def import_url(
    url: str = Form(...),
    title: str = Form(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Ingest web documentation or YouTube educational lecture via asynchronous background worker.
    Includes strict Anti-SSRF URL validation to prevent unauthorized internal network scanning.
    """
    clean_url = url.strip()
    is_safe, error_msg = validate_safe_url(clean_url)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Security verification failed: {error_msg}"
        )

    doc_title = title or "Web Document"
    job_id = str(uuid.uuid4())
    job_manager.create_job(job_id, title=doc_title, filename=clean_url)

    background_tasks.add_task(
        _run_background_indexing,
        job_id=job_id,
        file_path=clean_url,
        title=doc_title,
        source_type="web",
        filename="web.html"
    )

    return JSONResponse(
        status_code=202,
        content={
            "status": "queued",
            "job_id": job_id,
            "message": f"URL '{doc_title}' queued for processing.",
            "title": doc_title,
            "filename": clean_url
        }
    )

@router.get("/status/{job_id}")
async def get_ingestion_status(job_id: str):
    """Poll the real-time progress and status of a queued or running ingestion job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Ingestion job '{job_id}' not found.")
    return job

@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a document and clears its real-time vector embeddings and BM25 index."""
    success = await offline_indexer.delete_document(doc_id=doc_id, db=db)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success", "message": f"Document {doc_id} deleted successfully"}

@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = res.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "source_type": d.source_type,
            "total_pages": d.total_pages,
            "status": d.status,
            "created_at": str(d.created_at)
        }
        for d in docs
    ]

@router.get("/document/{doc_id}/pages")
async def get_document_pages(doc_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PageImage).where(PageImage.document_id == doc_id).order_by(PageImage.page_number)
    )
    pages = res.scalars().all()
    return [
        {
            "id": p.id,
            "page_number": p.page_number,
            "image_path": p.image_path,
            "text_snippet": (p.extracted_text or "")[:200],
            "has_diagrams": p.has_diagrams,
            "has_equations": p.has_equations
        }
        for p in pages
    ]
