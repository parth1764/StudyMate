from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document
from app.quiz.generator import generate_quiz
from app.rag.vectorstore import get_vector_store
from app.schemas import QuizResponse

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/{document_id}", response_model=QuizResponse)
def quiz(
    document_id: str,
    num_questions: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "ready":
        raise HTTPException(status_code=409, detail=f"Document status is '{doc.status}', not ready")

    chunks = get_vector_store().get_document_chunks(document_id)
    questions = generate_quiz(chunks, num_questions=num_questions)
    return QuizResponse(document_id=document_id, questions=questions)
