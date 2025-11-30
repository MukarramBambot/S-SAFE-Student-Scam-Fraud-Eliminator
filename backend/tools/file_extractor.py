import logging
import io
from typing import Union
from pathlib import Path

# Strict imports
import pypdf
import docx

logger = logging.getLogger("backend.tools.extractor")

def extract_text(file_content: bytes, filename: str) -> str:
    """Extract text from PDF, DOCX, or TXT content."""
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith(".pdf"):
            return _extract_pdf(file_content)
        
        elif filename_lower.endswith(".docx"):
            return _extract_docx(file_content)
        
        elif filename_lower.endswith(".txt"):
            return file_content.decode("utf-8", errors="ignore")
        
        else:
            return f"[Unsupported file type: {filename}]"

    except Exception as e:
        logger.error("Failed to extract text from %s: %s", filename, e)
        return f"[Error extracting file: {str(e)}]"

def _extract_pdf(content: bytes) -> str:
    text = []
    try:
        with io.BytesIO(content) as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    except Exception as e:
        raise RuntimeError(f"PDF parsing error: {e}")

def _extract_docx(content: bytes) -> str:
    try:
        with io.BytesIO(content) as f:
            doc = docx.Document(f)
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        raise RuntimeError(f"DOCX parsing error: {e}")
