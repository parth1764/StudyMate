from datetime import datetime

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    doc_type: str
    num_chunks: int
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class YouTubeIngestRequest(BaseModel):
    url: str = Field(..., min_length=1)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    document_id: str | None = Field(
        default=None, description="Restrict retrieval to one document; omit to search the whole corpus."
    )
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class SummarizeResponse(BaseModel):
    document_id: str
    summary: str


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizResponse(BaseModel):
    document_id: str
    questions: list[QuizQuestion]
