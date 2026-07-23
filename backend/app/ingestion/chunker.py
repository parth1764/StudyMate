"""Simple sliding-window character chunker.

Splits on paragraph/sentence boundaries where possible so chunks stay
semantically coherent, while keeping a fixed overlap for retrieval recall.
"""

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []

    sentences = _SENTENCE_SPLIT.split(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            if len(sentence) > chunk_size:
                # Sentence itself too long: hard-split it.
                for i in range(0, len(sentence), chunk_size - chunk_overlap):
                    chunks.append(sentence[i : i + chunk_size])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    if chunk_overlap and len(chunks) > 1:
        overlapped = [chunks[0]]
        for chunk in chunks[1:]:
            prev_tail = overlapped[-1][-chunk_overlap:]
            overlapped.append(f"{prev_tail} {chunk}".strip())
        return overlapped

    return chunks
