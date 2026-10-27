import os
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from rank_bm25 import BM25Okapi
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.models import Document, PageImage, Chunk, Concept
from app.core.embeddings import embedding_service
from app.core.vector_db import vector_store
from app.pipeline.offline.parser import dual_parser
from app.pipeline.offline.chunker import contextual_chunker
from app.pipeline.offline.graph_extractor import graph_extractor

logger = logging.getLogger(__name__)

class BM25SearchEngine:
    def __init__(self):
        self.corpus_chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None

    def index(self, chunks: List[Dict[str, Any]]):
        self.corpus_chunks.extend(chunks)
        tokenized_corpus = [
            (c.get("contextual_line", "") + " " + c.get("content", "")).lower().split()
            for c in self.corpus_chunks
        ]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

    def remove_document(self, doc_id: str):
        self.corpus_chunks = [c for c in self.corpus_chunks if c.get("doc_id") != doc_id]
        tokenized_corpus = [
            (c.get("contextual_line", "") + " " + c.get("content", "")).lower().split()
            for c in self.corpus_chunks
        ]
        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.corpus_chunks:
            return []
        tokenized_query = query.lower().split()
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if doc_scores[idx] > 0.0:
                c = self.corpus_chunks[idx].copy()
                c["score"] = float(doc_scores[idx])
                results.append(c)
        return results

    def get_chunks_by_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves in-memory chunks by their IDs.
        """
        chunk_set = set(chunk_ids)
        return [
            c.copy() for c in self.corpus_chunks
            if c.get("id") in chunk_set or c.get("chunk_id") in chunk_set
        ]

bm25_engine = BM25SearchEngine()

class OfflineIndexer:
    async def index_source(
        self,
        file_path_or_content: str,
        title: str,
        source_type: str,
        db: AsyncSession,
        original_filename: str = "",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Unified real-time offline pipeline execution for any source:
        - PDF textbooks & papers
        - Image diagrams, handwritten notes, snapshots (PNG, JPG, WEBP, BMP)
        - DOCX notes & PPTX slides
        - Raw text or markdown notes
        - Web URLs & YouTube lectures
        """
        if progress_callback:
            progress_callback(10, "Parsing document structure and pages...")

        doc_id = str(uuid.uuid4())
        ext = os.path.splitext(original_filename or file_path_or_content)[1].lower()

        # Determine concrete source type and parse pages
        if source_type == "image" or ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
            source_type = "image"
            pages_data = await dual_parser.parse_image(file_path_or_content, doc_id=doc_id, title=title)
        elif source_type == "docx" or ext in [".docx", ".doc"]:
            source_type = "docx"
            pages_data = dual_parser.parse_docx(file_path_or_content)
        elif source_type == "pptx" or ext in [".pptx", ".ppt"]:
            source_type = "pptx"
            pages_data = dual_parser.parse_pptx(file_path_or_content)
        elif source_type == "web" or file_path_or_content.startswith("http"):
            if "youtube.com" in file_path_or_content or "youtu.be" in file_path_or_content:
                source_type = "video"
                title_yt, pages_data = await dual_parser.parse_youtube(file_path_or_content)
                title = title or title_yt
            else:
                source_type = "web"
                w_title, clean_text = dual_parser.parse_web(file_path_or_content)
                title = title or w_title
                pages_data = dual_parser.parse_text(clean_text, title=title)
        elif source_type in ["text", "note", "md"] or ext in [".txt", ".md"]:
            source_type = "note"
            if os.path.isfile(file_path_or_content):
                with open(file_path_or_content, "r", encoding="utf-8", errors="ignore") as f:
                    content_str = f.read()
            else:
                content_str = file_path_or_content
            pages_data = dual_parser.parse_text(content_str, title=title)
        else:
            # Default to PDF
            source_type = "pdf"
            pages_data = dual_parser.parse_pdf(file_path_or_content, doc_id)

        if progress_callback:
            progress_callback(30, f"Extracted {len(pages_data)} pages. Creating contextual chunks...")

        # Create Document in DB
        db_doc = Document(
            id=doc_id,
            title=title,
            source_type=source_type,
            file_path=file_path_or_content if os.path.exists(file_path_or_content) else None,
            total_pages=len(pages_data),
            status="processing"
        )
        db.add(db_doc)
        await db.commit()

        # Save PageImages in DB
        for p in pages_data:
            page_record = PageImage(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                page_number=p["page_number"],
                image_path=p.get("image_path", ""),
                extracted_text=p.get("text", ""),
                has_diagrams=p.get("has_diagrams", False),
                has_equations=p.get("has_equations", False)
            )
            db.add(page_record)
        await db.commit()

        # 2. Contextual Hierarchical Chunks
        raw_chunks = contextual_chunker.create_hierarchical_chunks(pages_data)
        enriched_chunks = await contextual_chunker.add_context_lines(raw_chunks, doc_title=title)

        if progress_callback:
            progress_callback(55, f"Created {len(enriched_chunks)} chunks. Generating embeddings & concept graph concurrently...")

        # Pre-assign UUID chunk IDs for deterministic alignment across vector store and graph
        all_chunk_ids = []
        for i, c in enumerate(enriched_chunks):
            chunk_id = str(uuid.uuid4())
            c["id"] = chunk_id
            c["doc_id"] = doc_id
            c["doc_title"] = title
            all_chunk_ids.append(chunk_id)

        # 3. Prepare Embeddings & Extract Concept Graph Concurrently
        texts_to_embed = [
            f"{c.get('contextual_line', '')}\n\n{c['content']}"
            for c in enriched_chunks
        ]
        combined_sample_text = "\n\n".join([p["text"] for p in pages_data[:5]])

        # Execute CPU-bound batch embeddings in thread pool while Gemini concept extraction runs concurrently
        embed_task = asyncio.to_thread(embedding_service.embed_documents, texts_to_embed, 32)
        kg_task = graph_extractor.extract_and_store(
            combined_sample_text,
            domain=title,
            source_chunk_ids=all_chunk_ids
        )
        dense_vectors, kg_result = await asyncio.gather(embed_task, kg_task)

        if progress_callback:
            progress_callback(80, "Storing extracted graph nodes and vectors...")

        # Store extracted concepts in relational DB
        for cp in kg_result.concepts:
            existing_c = await db.execute(select(Concept).where(Concept.name.ilike(cp.name)))
            if not existing_c.scalars().first():
                db_c = Concept(
                    name=cp.name,
                    description=cp.description,
                    domain=cp.domain or title,
                    base_difficulty=cp.difficulty
                )
                db.add(db_c)
        await db.commit()

        qdrant_points = []
        for i, c in enumerate(enriched_chunks):
            chunk_id = c["id"]

            # DB chunk record
            db_chunk = Chunk(
                id=chunk_id,
                document_id=doc_id,
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                section_title=c.get("section_title", f"Page {c['page_number']}"),
                content=c["content"],
                contextual_line=c.get("contextual_line", ""),
                difficulty_score=c.get("difficulty_score", 0.5),
                token_count=c.get("token_count", 0),
                primary_concepts=[cp.name for cp in kg_result.concepts[:3]]
            )
            db.add(db_chunk)

            qdrant_points.append({
                "id": chunk_id,
                "vector": dense_vectors[i],
                "payload": {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "doc_title": title,
                    "page_number": c["page_number"],
                    "section_title": c.get("section_title", f"Page {c['page_number']}"),
                    "content": c["content"],
                    "contextual_line": c.get("contextual_line", ""),
                    "difficulty_score": c.get("difficulty_score", 0.5),
                    "concepts": [cp.name for cp in kg_result.concepts]
                }
            })

        # Upsert to Qdrant Dense Vector Store immediately
        vector_store.upsert_chunks(qdrant_points)
        
        # Index in BM25 Sparse Engine immediately
        bm25_engine.index(enriched_chunks)

        # 5. Build Graph Communities and Pre-compute Summaries (Microsoft GraphRAG Style)
        community_summaries = await graph_extractor.build_and_summarize_communities(domain=title)

        db_doc.status = "indexed"
        await db.commit()

        if progress_callback:
            progress_callback(100, "Knowledge base indexing complete!")

        logger.info(
            "Successfully indexed source '%s' (%s): %d pages, %d chunks, %d concepts, %d communities.",
            title, source_type, len(pages_data), len(enriched_chunks), len(kg_result.concepts), len(community_summaries)
        )

        return {
            "document_id": doc_id,
            "title": title,
            "source_type": source_type,
            "pages": len(pages_data),
            "chunks": len(enriched_chunks),
            "concepts_extracted": len(kg_result.concepts),
            "misconceptions_extracted": len(kg_result.misconceptions),
            "communities_created": len(community_summaries)
        }

    async def index_pdf(self, pdf_path: str, title: str, db: AsyncSession) -> Dict[str, Any]:
        """Backward-compatible shortcut for PDF indexing."""
        return await self.index_source(
            file_path_or_content=pdf_path,
            title=title,
            source_type="pdf",
            db=db,
            original_filename=os.path.basename(pdf_path)
        )

    async def delete_document(self, doc_id: str, db: AsyncSession) -> bool:
        """Deletes document, its vector points in Qdrant, BM25 tokens, and database records."""
        res = await db.execute(select(Document).where(Document.id == doc_id))
        doc = res.scalars().first()
        if not doc:
            return False

        # 1. Delete vectors from Qdrant
        vector_store.delete_document_chunks(doc_id)

        # 2. Remove chunks from BM25
        bm25_engine.remove_document(doc_id)

        # 3. Delete from DB (cascades to PageImage & Chunk)
        await db.delete(doc)
        await db.commit()
        logger.info("Deleted document %s from DB and vector stores.", doc_id)
        return True

    async def sync_all_from_db(self, db: AsyncSession):
        """Loads all existing DB chunks into BM25 on startup so search is immediately warm."""
        res = await db.execute(select(Chunk, Document.title).join(Document, Chunk.document_id == Document.id))
        rows = res.all()
        chunks_to_index = []
        for chunk, doc_title in rows:
            chunks_to_index.append({
                "id": chunk.id,
                "doc_id": chunk.document_id,
                "doc_title": doc_title,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
                "content": chunk.content,
                "contextual_line": chunk.contextual_line,
                "difficulty_score": chunk.difficulty_score
            })
        if chunks_to_index:
            bm25_engine.index(chunks_to_index)
            logger.info("Loaded and synchronized %d chunks into BM25 search engine.", len(chunks_to_index))

offline_indexer = OfflineIndexer()

