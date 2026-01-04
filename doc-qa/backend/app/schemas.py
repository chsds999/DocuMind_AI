from pydantic import BaseModel, Field
from typing import List, Optional


class IngestResponse(BaseModel):
    doc_id: str
    pages: int
    chunks: int


class AskRequest(BaseModel):
    doc_id: str
    question: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=5, ge=1, le=15)


class Citation(BaseModel):
    page: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_chunks: Optional[int] = None
