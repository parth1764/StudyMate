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
from app.models import Document
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import get_vector_store
from app.schemas import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])


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

    try:
        text = extract_text(dest_path)
        if not text.strip():
            raise ValueError("No extractable text found in the uploaded file.")

        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        vectors = embed_texts(chunks)

        metadatas = [
            {
                "document_id": document_id,
                "filename": file.filename,
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
    ext = Path(doc.filename).suffix.lower()
    upload_file = settings.uploads_path / f"{document_id}{ext}"
    upload_file.unlink(missing_ok=True)

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}
