"""FAISS-backed vector store with a JSON metadata sidecar.

Single-process, in-memory index flushed to disk after every write. That's
the right tradeoff for a personal/single-user project; see README for the
concurrency caveat before using this for multi-user production traffic.
"""

import json
import threading
from pathlib import Path

import faiss
import numpy as np

from app.config import get_settings

_INDEX_FILE = "vectors.faiss"
_META_FILE = "metadata.json"

_lock = threading.Lock()


class VectorStore:
    def __init__(self, dim: int, index_dir: Path):
        self.dim = dim
        self.index_dir = index_dir
        self.index_path = index_dir / _INDEX_FILE
        self.meta_path = index_dir / _META_FILE

        self.metadata: dict[int, dict] = {}
        self.next_id = 0

        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            raw = json.loads(self.meta_path.read_text())
            self.next_id = raw["next_id"]
            self.metadata = {int(k): v for k, v in raw["items"].items()}
        else:
            flat = faiss.IndexFlatIP(dim)
            self.index = faiss.IndexIDMap2(flat)

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        payload = {"next_id": self.next_id, "items": self.metadata}
        self.meta_path.write_text(json.dumps(payload))

    def add(self, vectors: np.ndarray, metadatas: list[dict]) -> list[int]:
        with _lock:
            ids = np.arange(self.next_id, self.next_id + len(metadatas), dtype="int64")
            self.index.add_with_ids(vectors, ids)
            for i, meta in zip(ids, metadatas):
                self.metadata[int(i)] = meta
            self.next_id += len(metadatas)
            self._persist()
            return ids.tolist()

    def search(
        self, query_vector: np.ndarray, top_k: int, document_id: str | None = None
    ) -> list[dict]:
        if self.index.ntotal == 0:
            return []

        # Over-fetch when filtering by document so we still return top_k
        # results after dropping non-matching rows.
        fetch_k = top_k * 5 if document_id else top_k
        fetch_k = min(fetch_k, self.index.ntotal)

        scores, ids = self.index.search(query_vector.reshape(1, -1), fetch_k)
        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            meta = self.metadata.get(int(idx))
            if meta is None:
                continue
            if document_id and meta["document_id"] != document_id:
                continue
            results.append({**meta, "score": float(score)})
            if len(results) >= top_k:
                break
        return results

    def get_document_chunks(self, document_id: str) -> list[str]:
        items = [m for m in self.metadata.values() if m["document_id"] == document_id]
        items.sort(key=lambda m: m["chunk_index"])
        return [m["text"] for m in items]

    def delete_document(self, document_id: str) -> None:
        with _lock:
            ids_to_remove = [
                i for i, meta in self.metadata.items() if meta["document_id"] == document_id
            ]
            if not ids_to_remove:
                return
            self.index.remove_ids(np.array(ids_to_remove, dtype="int64"))
            for i in ids_to_remove:
                del self.metadata[i]
            self._persist()


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        from app.rag.embeddings import get_embedder

        dim = get_embedder().get_sentence_embedding_dimension()
        settings = get_settings()
        _store = VectorStore(dim=dim, index_dir=settings.index_path)
    return _store
