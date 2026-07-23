"""Local, CPU-only summarization via DistilBART.

Long documents are handled with a simple map-reduce: chunks are grouped into
batches that fit the model's ~1024 token context, each batch is summarized,
and if more than one batch resulted, the partial summaries are summarized
again (recursively) until a single summary remains.
"""

from functools import lru_cache

from transformers import pipeline

from app.config import get_settings

# ~4 chars/token heuristic keeps each batch comfortably under BART's 1024
# token limit, leaving headroom for special tokens.
_MAX_CHARS_PER_BATCH = 3000


@lru_cache
def get_summarizer():
    settings = get_settings()
    return pipeline(
        "summarization",
        model=settings.summarization_model,
        device=-1,  # force CPU
    )


def _summarize_text(text: str) -> str:
    summarizer = get_summarizer()
    input_len = len(text.split())
    max_len = max(20, min(142, int(input_len * 0.6)))
    min_len = max(10, int(max_len * 0.4))
    result = summarizer(
        text,
        max_length=max_len,
        min_length=min_len,
        do_sample=False,
        truncation=True,
    )
    return result[0]["summary_text"].strip()


def _group_chunks(chunks: list[str], max_chars: int) -> list[str]:
    groups: list[str] = []
    current = ""
    for chunk in chunks:
        if current and len(current) + len(chunk) + 1 > max_chars:
            groups.append(current)
            current = chunk
        else:
            current = f"{current} {chunk}".strip()
    if current:
        groups.append(current)
    return groups


def summarize_document(chunks: list[str]) -> str:
    if not chunks:
        return ""

    groups = _group_chunks(chunks, _MAX_CHARS_PER_BATCH)
    partial_summaries = [_summarize_text(g) for g in groups]

    if len(partial_summaries) == 1:
        return partial_summaries[0]

    # Reduce step: summarize the concatenation of partial summaries,
    # recursing if that concatenation is itself too long.
    return summarize_document(partial_summaries)
