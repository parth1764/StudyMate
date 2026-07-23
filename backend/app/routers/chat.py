from fastapi import APIRouter

from app.rag.pipeline import answer_question
from app.schemas import AskRequest, AskResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    answer, sources = answer_question(
        question=request.question,
        document_id=request.document_id,
        top_k=request.top_k,
    )
    return AskResponse(answer=answer, sources=sources)
