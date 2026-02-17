"""PDF text extraction service using pypdf and pdfplumber.

Extracts text content from PDF files for question generation.
Uses multiple extraction strategies for best results:
  1. pdfplumber (best for tables and structured content)
  2. pypdf (fallback for simple text)
"""
import io
import logging
from pathlib import Path
from typing import Optional, List, Dict

# Try to import pdfplumber, but make it optional for Railway deployment
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("pdfplumber not available - will use pypdf only")

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Handles PDF text extraction with multiple strategies."""

    def extract_text(self, pdf_file: bytes, filename: str = "unknown.pdf") -> Optional[str]:
        """Extract all text from a PDF file.

        Args:
            pdf_file: PDF file content as bytes
            filename: Original filename for logging

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Try pdfplumber first if available (better for structured content)
            if PDFPLUMBER_AVAILABLE:
                text = self._extract_with_pdfplumber(pdf_file)
                if text and len(text.strip()) > 100:
                    logger.info(f"Extracted {len(text)} chars from {filename} using pdfplumber")
                    return text

            # Fallback to pypdf
            text = self._extract_with_pypdf2(pdf_file)
            if text and len(text.strip()) > 100:
                logger.info(f"Extracted {len(text)} chars from {filename} using pypdf")
                return text

            logger.warning(f"No text extracted from {filename}")
            return None

        except Exception as e:
            logger.error(f"PDF extraction failed for {filename}: {e}")
            return None

    def extract_by_pages(
        self, pdf_file: bytes, filename: str = "unknown.pdf", page_limit: int = 50
    ) -> List[Dict[str, any]]:
        """Extract text page by page for chunked processing.

        Args:
            pdf_file: PDF file content as bytes
            filename: Original filename for logging
            page_limit: Maximum pages to extract (prevents huge PDFs)

        Returns:
            List of dicts with {page_num, text}
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available - cannot extract by pages, using fallback")
            # Fallback: extract all text and return as single page
            text = self.extract_text(pdf_file, filename)
            if text:
                return [{"page_num": 1, "text": text, "char_count": len(text)}]
            return []

        pages = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                total_pages = min(len(pdf.pages), page_limit)

                for page_num, page in enumerate(pdf.pages[:total_pages], start=1):
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        pages.append({
                            "page_num": page_num,
                            "text": self._clean_text(text),
                            "char_count": len(text)
                        })

                logger.info(f"Extracted {len(pages)} pages from {filename}")
                return pages

        except Exception as e:
            logger.error(f"Page extraction failed for {filename}: {e}")
            return []

    def _extract_with_pdfplumber(self, pdf_file: bytes) -> Optional[str]:
        """Extract text using pdfplumber (best for tables)."""
        try:
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                full_text = "\n\n".join(text_parts)
                return self._clean_text(full_text)

        except Exception as e:
            logger.debug(f"pdfplumber extraction failed: {e}")
            return None

    def _extract_with_pypdf2(self, pdf_file: bytes) -> Optional[str]:
        """Extract text using pypdf (fallback)."""
        try:
            reader = PdfReader(io.BytesIO(pdf_file))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)
            return self._clean_text(full_text)

        except Exception as e:
            logger.debug(f"pypdf extraction failed: {e}")
            return None

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text (remove excessive whitespace, etc.)."""
        # Replace multiple newlines with double newline
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines).strip()

    def get_pdf_info(self, pdf_file: bytes) -> Dict[str, any]:
        """Get metadata about the PDF.

        Returns:
            Dict with page_count, file_size, etc.
        """
        if not PDFPLUMBER_AVAILABLE:
            # Fallback: use pypdf to get page count
            try:
                reader = PdfReader(io.BytesIO(pdf_file))
                return {
                    "page_count": len(reader.pages),
                    "file_size_kb": len(pdf_file) / 1024,
                    "metadata": reader.metadata or {},
                }
            except Exception as e:
                logger.error(f"Failed to get PDF info with pypdf: {e}")
                return {"page_count": 0, "file_size_kb": 0, "metadata": {}}

        try:
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                return {
                    "page_count": len(pdf.pages),
                    "file_size_kb": len(pdf_file) / 1024,
                    "metadata": pdf.metadata or {},
                }
        except Exception as e:
            logger.error(f"Failed to get PDF info: {e}")
            return {"page_count": 0, "file_size_kb": 0, "metadata": {}}


# Singleton
pdf_extractor = PDFExtractor()
