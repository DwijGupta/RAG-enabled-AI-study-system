import os
import uuid
import logging
import asyncio
from typing import List, Dict, Any, Tuple, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz  # Fallback for older installations
import pymupdf4llm
import trafilatura
import yt_dlp
from app.core.config import settings
from app.core.gemini_client import gemini_client

logger = logging.getLogger(__name__)

class DualParser:
    """
    Dual-Engine Ingestion Pipeline:
    1. PDFs / Academic Papers / Textbooks:
       - Docling (by IBM): Recovers multi-column reading order, tables, headers, and LaTeX math.
       - PyMuPDF: Concurrently renders crisp 150 DPI page PNG snapshots for the visual citation inspector.
    2. Slide Decks (PPTX) & Notes (DOCX):
       - Docling: High-fidelity structured markdown extraction.
    3. Web Articles & Papers:
       - Trafilatura: Clean web text extraction without boilerplate/ads.
    4. YouTube & Audio Lectures:
       - yt-dlp: Audio extraction.
       - Google Gemini: Multimodal audio transcription with technical accuracy and timestamps (replaces Whisper).
    """
    def __init__(self):
        self.pages_dir = os.path.join(settings.STORAGE_DIR, "pages")
        self.audio_dir = os.path.join(settings.STORAGE_DIR, "audio")
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self._docling_converter = None

    @property
    def docling_converter(self):
        if self._docling_converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._docling_converter = DocumentConverter()
                logger.info("Docling DocumentConverter initialized successfully.")
            except Exception as e:
                logger.warning("Docling initialization deferred: %s", str(e))
                self._docling_converter = None
        return self._docling_converter

    def parse_pdf(self, pdf_path: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        Parses PDF using Dual Engine:
        - PyMuPDF renders 150 DPI page PNGs for visual inspection.
        - Docling (with PyMuPDF4LLM fallback) extracts structured Markdown with tables and LaTeX math.
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_data = []

        # 1. First pass: PyMuPDF page rendering & visual element detection
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Render page image (150 DPI for crisp visual page inspector)
            pix = page.get_pixmap(dpi=150)
            image_filename = f"{doc_id}_page_{page_num}.png"
            image_path = os.path.join(self.pages_dir, image_filename)
            pix.save(image_path)

            image_list = page.get_images()
            drawings = page.get_drawings()
            has_visuals = len(image_list) > 0 or len(drawings) > 3

            # Baseline text from PyMuPDF
            raw_text = page.get_text("text").strip()

            pages_data.append({
                "page_number": page_num,
                "text": raw_text,
                "image_path": f"/storage/pages/{image_filename}",
                "local_image_path": image_path,
                "has_diagrams": has_visuals,
                "has_equations": "$" in raw_text or "=" in raw_text or "∑" in raw_text
            })

        doc.close()

        # 2. Second pass: Docling structured extraction (LaTeX formulas, tables, reading order)
        try:
            if self.docling_converter:
                logger.info("Extracting structured markdown via Docling for %s...", pdf_path)
                conv_res = self.docling_converter.convert(pdf_path)
                docling_md = conv_res.document.export_to_markdown()

                if docling_md and len(docling_md.strip()) > 50:
                    # Enrich pages_data with Docling's high-fidelity markdown
                    # If single page or short doc, assign markdown directly
                    if total_pages == 1:
                        pages_data[0]["text"] = docling_md
                        pages_data[0]["has_equations"] = "$" in docling_md or "=" in docling_md
                    else:
                        # Split by markdown headers or keep structured document chunks
                        md_sections = docling_md.split("\n## ")
                        if len(md_sections) >= total_pages:
                            for idx in range(min(total_pages, len(md_sections))):
                                prefix = "## " if idx > 0 else ""
                                pages_data[idx]["text"] = prefix + md_sections[idx]
                        else:
                            # Use PyMuPDF4LLM per-page markdown chunks
                            md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
                            for idx, chunk in enumerate(md_pages):
                                if idx < len(pages_data):
                                    pages_data[idx]["text"] = chunk.get("text", pages_data[idx]["text"])
            else:
                # Fallback to PyMuPDF4LLM
                md_pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
                for idx, chunk in enumerate(md_pages):
                    if idx < len(pages_data):
                        pages_data[idx]["text"] = chunk.get("text", pages_data[idx]["text"])

        except Exception as e:
            logger.warning("Docling extraction notice: %s. Using PyMuPDF extracted text.", str(e))

        logger.info("Parsed PDF %s with %d pages and rendered images.", pdf_path, len(pages_data))
        return pages_data

    def parse_docx(self, docx_path: str) -> List[Dict[str, Any]]:
        """Parses DOCX document into structured Markdown using Docling."""
        logger.info("Parsing DOCX via Docling: %s", docx_path)
        try:
            if self.docling_converter:
                conv_res = self.docling_converter.convert(docx_path)
                md = conv_res.document.export_to_markdown()
                return self.parse_text(md, title=os.path.basename(docx_path))
        except Exception as e:
            logger.error("Docling DOCX parse error: %s", str(e))
        return self.parse_text(f"DOCX Document: {os.path.basename(docx_path)}")

    def parse_pptx(self, pptx_path: str) -> List[Dict[str, Any]]:
        """Parses PPTX presentation slides into structured Markdown using Docling."""
        logger.info("Parsing PPTX via Docling: %s", pptx_path)
        try:
            if self.docling_converter:
                conv_res = self.docling_converter.convert(pptx_path)
                md = conv_res.document.export_to_markdown()
                return self.parse_text(md, title=os.path.basename(pptx_path))
        except Exception as e:
            logger.error("Docling PPTX parse error: %s", str(e))
        return self.parse_text(f"PPTX Slide Deck: {os.path.basename(pptx_path)}")

    def parse_web(self, url: str) -> Tuple[str, str]:
        """
        Ingests web article via trafilatura.
        Returns (title, clean_text)
        """
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Failed to fetch content from URL: {url}")
        
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if metadata and metadata.title else url
        return title, text or ""

    def parse_text(self, content: str, title: str = "Notes") -> List[Dict[str, Any]]:
        """Parses raw text or markdown notes into a pseudo-page structure."""
        return [{
            "page_number": 1,
            "text": content,
            "image_path": "",
            "local_image_path": "",
            "has_diagrams": False,
            "has_equations": "$" in content or "=" in content or "∑" in content
        }]

    async def parse_audio(self, audio_path: str, title: str = "Audio Lecture") -> List[Dict[str, Any]]:
        """
        Transcribes audio lecture using Google Gemini multimodal audio understanding (Whisper replacement).
        Returns list of structured pseudo-pages.
        """
        logger.info("Transcribing audio lecture via Google Gemini: %s", audio_path)
        transcript = await gemini_client.transcribe_audio(audio_path)
        return [{
            "page_number": 1,
            "text": transcript,
            "image_path": "",
            "local_image_path": "",
            "has_diagrams": False,
            "has_equations": "$" in transcript or "=" in transcript or "∑" in transcript
        }]

    async def parse_youtube(self, url: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts YouTube lecture audio via yt-dlp, then transcribes using Google Gemini (Whisper replacement).
        Returns (video_title, pages_data)
        """
        logger.info("Downloading YouTube lecture audio via yt-dlp: %s", url)
        out_tmpl = os.path.join(self.audio_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': out_tmpl,
            'quiet': True,
            'no_warnings': True
        }

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'YouTube Educational Lecture')
                video_id = info.get('id', 'video')
                ext = info.get('ext', 'mp3')
                audio_file = os.path.join(self.audio_dir, f"{video_id}.{ext}")
                return title, audio_file

        title, audio_file = await asyncio.to_thread(_extract)
        pages_data = await self.parse_audio(audio_file, title=title)
        return title, pages_data

    async def parse_image(self, image_path: str, doc_id: str, title: str = "Image Source") -> List[Dict[str, Any]]:
        """
        Parses an academic image, diagram, slide snapshot, or handwritten notes:
        1. Copies image to pages storage as {doc_id}_page_1.png so UI Page Inspector and EvidencePanel can view it.
        2. Performs multimodal visual analysis using Gemini to extract verbatim text, LaTeX math, and diagram descriptions.
        3. Returns structured page data ready for chunking and real-time embedding.
        """
        import shutil
        from PIL import Image

        image_filename = f"{doc_id}_page_1.png"
        target_page_path = os.path.join(self.pages_dir, image_filename)
        
        # Save as PNG for uniform page inspector viewing
        try:
            with Image.open(image_path) as img:
                img.convert("RGB").save(target_page_path, "PNG")
        except Exception:
            shutil.copyfile(image_path, target_page_path)

        # Detect mime type
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".gif": "image/gif"
        }
        mime_type = mime_map.get(ext, "image/png")

        # Multimodal Gemini Analysis
        extracted_text = ""
        try:
            logger.info("Performing multimodal visual analysis on image: %s", image_path)
            extracted_text = await gemini_client.analyze_image(
                image_path_or_bytes=image_path,
                mime_type=mime_type,
                prompt=(
                    f"You are an academic document parser. Transcribe and extract all educational content from this image ({title}):\n"
                    "1. Extract all text verbatim with clear markdown formatting.\n"
                    "2. Convert all mathematical equations or formulas into LaTeX enclosed in $$ or $.\n"
                    "3. If this contains a diagram, flowchart, chart, or architecture, describe all its components, nodes, labels, and relationships in detail.\n"
                    "4. Provide a conceptual summary of the topics covered."
                )
            )
        except Exception as e:
            logger.warning("Gemini image analysis notice: %s. Using fallback image metadata.", str(e))
            extracted_text = f"### Academic Image Source: {title}\n\n[Diagram / Visual Content from {os.path.basename(image_path)}]"

        has_equations = "$" in extracted_text or "=" in extracted_text or "∑" in extracted_text

        return [{
            "page_number": 1,
            "text": extracted_text,
            "image_path": f"/storage/pages/{image_filename}",
            "local_image_path": target_page_path,
            "has_diagrams": True,
            "has_equations": has_equations
        }]

dual_parser = DualParser()

