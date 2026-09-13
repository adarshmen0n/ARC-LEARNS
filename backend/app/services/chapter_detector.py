"""Chapter and section detector for ARC LEARNS."""

import re
from typing import List


def detect_chapters(text: str) -> List[str]:
    """Detect chapters, main topics, or sections from educational text."""
    if not text:
        return []

    # Check for Markdown headers: # or ##
    md_pattern = r"(?:^|\n)(#{1,3}\s+[^\n]+(?:\n(?:(?!#{1,3}\s+).)*)*)"
    md_matches = re.findall(md_pattern, text, re.DOTALL)
    if len(md_matches) >= 2:
        return [m.strip() for m in md_matches if m.strip()]

    # Check for Chapter pattern: Chapter 1, Chapter 2
    chapter_pattern = r"(Chapter\s+\d+.*?)(?=Chapter\s+\d+|$)"
    ch_matches = re.findall(chapter_pattern, text, re.DOTALL | re.IGNORECASE)
    if len(ch_matches) >= 2:
        return [m.strip() for m in ch_matches if m.strip()]

    # Check for Numbered sections: 1. Introduction, 2. Background
    num_pattern = r"(?:^|\n)(\d+\.\s+[A-Z][^\n]+(?:\n(?!\d+\.\s+[A-Z]).)*)"
    num_matches = re.findall(num_pattern, text, re.DOTALL)
    if len(num_matches) >= 2:
        return [m.strip() for m in num_matches if m.strip()]

    # Fallback: Split by large paragraph groups or return complete text
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
    if len(paragraphs) >= 3:
        # Group into 3-4 coherent chapters
        step = max(1, len(paragraphs) // 3)
        return ["\n\n".join(paragraphs[i:i + step]) for i in range(0, len(paragraphs), step)]

    return [text]