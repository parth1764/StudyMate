from app.config import get_settings
from app.llm.groq_client import chat_completion
from app.rag.embeddings import embed_query
from app.rag.vectorstore import get_vector_store
from app.schemas import SourceChunk

SYSTEM_PROMPT = (
    "You are StudyMate, an AI study assistant. Answer the user's question using "
    "ONLY the provided context excerpts. If the answer isn't in the context, say "
    "you don't have enough information from the uploaded material instead of "
    "guessing. Be concise and cite which excerpt(s) you used by number."
)


def _build_prompt(question: str, chunks: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[Excerpt {i+1} — {c['filename']}]\n{c['text']}" for i, c in enumerate(chunks)
    )
    return (
        f"Context excerpts:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the excerpts above."
    )


def answer_question(
    question: str, document_id: str | None = None, top_k: int | None = None
) -> tuple[str, list[SourceChunk]]:
    settings = get_settings()
    k = top_k or settings.top_k

    store = get_vector_store()
    query_vec = embed_query(question)
    hits = store.search(query_vec, top_k=k, document_id=document_id)

    if not hits:
        return (
            "No documents have been indexed yet (or none matched), so I have "
            "no material to answer from. Upload a document first.",
            [],
        )

    prompt = _build_prompt(question, hits)
    answer = chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )

    sources = [
        SourceChunk(
            document_id=h["document_id"],
            filename=h["filename"],
            chunk_index=h["chunk_index"],
            text=h["text"],
            score=h["score"],
        )
        for h in hits
    ]
    return answer, sources
