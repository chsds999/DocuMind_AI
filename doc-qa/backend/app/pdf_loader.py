from pypdf import PdfReader
from typing import List, Dict
from .utils import clean_whitespace


def extract_pages(pdf_path: str) -> List[Dict]:
    """
    Returns a list of dicts: { "page": int (1-based), "text": str }
    """
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = clean_whitespace(text)
        if text:
            pages.append({"page": i + 1, "text": text})
    return pages


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    """
    Simple character-based chunking (good enough for v1).
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be > overlap")

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if end == n:
            break
    return chunks
