from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import get_settings


@lru_cache
def get_embedder() -> SentenceTransformer:
    settings = get_settings()
    # device="cpu" is explicit: this project targets CPU-only inference.
    return SentenceTransformer(settings.embedding_model, device="cpu")


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_embedder()
    vectors = model.encode(
        texts,
        batch_size=16,
        show_progress_bar=False,
        normalize_embeddings=True,  # so inner product == cosine similarity
        convert_to_numpy=True,
    )
    return vectors.astype("float32")


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])[0]
