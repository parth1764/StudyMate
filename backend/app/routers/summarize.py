from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document
from app.rag.vectorstore import get_vector_store
from app.schemas import SummarizeResponse
from app.summarization.summarizer import summarize_document

router = APIRouter(prefix="/api/summarize", tags=["summarize"])


@router.post("/{document_id}", response_model=SummarizeResponse)
def summarize(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=409, detail=f"Document status is '{doc.status}', not ready")

    chunks = get_vector_store().get_document_chunks(document_id)
    summary = summarize_document(chunks)
    return SummarizeResponse(document_id=document_id, summary=summary)
