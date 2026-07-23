import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingestion.chunker import chunk_text
from app.ingestion.extractors import (
    SUPPORTED_EXTENSIONS,
    UnsupportedFileType,
    doc_type_for,
    extract_text,
)
from app.ingestion.youtube import YouTubeIngestError, extract_video_id, fetch_title, fetch_transcript
from app.models import Document
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import get_vector_store
from app.schemas import DocumentOut, YouTubeIngestRequest

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _index_document(doc: Document, text: str, db: Session) -> None:
    """Chunk, embed, and index already-extracted text for a Document row
    that has already been inserted with status='processing'."""
    settings = get_settings()
    try:
        if not text.strip():
            raise ValueError("No extractable text found.")

        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        vectors = embed_texts(chunks)

        metadatas = [
            {
                "document_id": doc.id,
                "filename": doc.filename,
                "chunk_index": i,
                "text": chunk,
            }
            for i, chunk in enumerate(chunks)
        ]
        get_vector_store().add(vectors, metadatas)

        doc.num_chunks = len(chunks)
        doc.status = "ready"
        db.commit()
    except (UnsupportedFileType, ValueError) as exc:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        doc.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


@router.post("/upload", response_model=DocumentOut)
def upload_document(file: UploadFile, db: Session = Depends(get_db)):
    settings = get_settings()
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    document_id = str(uuid.uuid4())
    dest_path = settings.uploads_path / f"{document_id}{ext}"
    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    doc = Document(
        id=document_id,
        filename=file.filename,
        doc_type=doc_type_for(ext),
        status="processing",
    )
    db.add(doc)
    db.commit()

    text = extract_text(dest_path)
    _index_document(doc, text, db)

    db.refresh(doc)
    return doc


@router.post("/youtube", response_model=DocumentOut)
def ingest_youtube(payload: YouTubeIngestRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        video_id = extract_video_id(payload.url)
        transcript = fetch_transcript(video_id)
    except YouTubeIngestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    title = fetch_title(video_id)

    document_id = str(uuid.uuid4())
    dest_path = settings.uploads_path / f"{document_id}.txt"
    dest_path.write_text(transcript, encoding="utf-8")

    doc = Document(
        id=document_id,
        filename=f"{title} (YouTube)",
        doc_type="youtube",
        status="processing",
    )
    db.add(doc)
    db.commit()

    _index_document(doc, transcript, db)

    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    get_vector_store().delete_document(document_id)

    settings = get_settings()
    for f in settings.uploads_path.glob(f"{document_id}.*"):
        f.unlink(missing_ok=True)

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
