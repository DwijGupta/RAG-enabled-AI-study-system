import os
import shutil
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_db
from app.core.models import Document, PageImage
from app.pipeline.offline.indexer import offline_indexer

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

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Real-time multi-format document and image ingestion pipeline:
    Accepts PDFs, Images (PNG, JPG, WEBP, BMP), DOCX notes, PPTX slides, and Markdown.
    Extracts text/visuals, builds concept graph, generates dense embeddings into Qdrant & BM25 in real time.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    detected_type = SUPPORTED_EXTENSIONS[ext]
    doc_title = title or file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    
    uploads_dir = os.path.join(settings.STORAGE_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = f"{os.urandom(8).hex()}_{file.filename}"
    upload_path = os.path.join(uploads_dir, safe_name)

    # Save uploaded file
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logger.info("Uploaded %s (%s): %s -> %s", detected_type, file.filename, file.filename, upload_path)

    try:
        # Run real-time multimodal knowledge-building pipeline
        result = await offline_indexer.index_source(
            file_path_or_content=upload_path,
            title=doc_title,
            source_type=detected_type,
            db=db,
            original_filename=file.filename
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error("Error processing file %s: %s", file.filename, str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Backward compatibility alias for PDF upload."""
    return await upload_file(file=file, title=title, db=db)

@router.post("/import-url")
async def import_url(
    url: str = Form(...),
    title: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Ingest web documentation or YouTube educational lecture via URL."""
    try:
        result = await offline_indexer.index_source(
            file_path_or_content=url.strip(),
            title=title or "Web Document",
            source_type="web",
            db=db,
            original_filename="web.html"
        )
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error("Error importing URL %s: %s", url, str(e))
        raise HTTPException(status_code=500, detail=f"Failed to import URL: {str(e)}")

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
