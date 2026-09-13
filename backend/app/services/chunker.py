"""Sentence and paragraph-aware chunking service for ARC LEARNS."""

import re
from typing import List


def create_chunks(text: str, chunk_size: int = 350, overlap: int = 50) -> List[str]:
    """Split text into coherent semantic chunks respecting paragraph and sentence boundaries."""
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[str] = []
    current_words: List[str] = []
    step = max(1, chunk_size - overlap)

    for para in paragraphs:
        words = para.split()
        if not words:
            continue

        if len(words) > chunk_size:
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = []
            for i in range(0, len(words), step):
                chunk_slice = words[i:i + chunk_size]
                if chunk_slice:
                    chunks.append(" ".join(chunk_slice))
                    if i + chunk_size >= len(words):
                        current_words = chunk_slice[-overlap:]
            continue

        if len(current_words) + len(words) > chunk_size and current_words:
            chunks.append(" ".join(current_words))
            current_words = current_words[-overlap:] + words
        else:
            current_words.extend(words)

    if current_words:
        chunks.append(" ".join(current_words))

    unique_chunks = []
    for c in chunks:
        c_clean = c.strip()
        if c_clean and (not unique_chunks or c_clean != unique_chunks[-1]):
            unique_chunks.append(c_clean)

    return unique_chunks


# Alias for backward and forward compatibility
chunk_text = create_chunks