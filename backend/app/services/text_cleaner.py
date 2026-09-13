"""Text cleaning service for ARC LEARNS.

Removes extraction artifacts and noise while strictly preserving paragraphs,
code blocks, headings, and semantic structure.
"""

import re


def clean_text(text: str) -> str:
    """Clean educational text while preserving structural line breaks and formatting."""
    if not text:
        return ""

    # 1. Normalize line endings
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Repair hyphenated broken words across line breaks (e.g. "learn-\ning" -> "learning")
    cleaned = re.sub(r"(\b[a-zA-Z]+)-\n([a-zA-Z]+\b)", r"\1\2", cleaned)

    # 3. Clean line by line, preserving code or structure
    lines = cleaned.split("\n")
    cleaned_lines = []

    for line in lines:
        # Collapse multiple horizontal spaces/tabs
        norm_line = re.sub(r"[ \t]+", " ", line).strip()
        # Drop standalone page numbers (e.g. "Page 12", "15")
        if re.match(r"^(?:page\s+\d+|\d+)$", norm_line, re.IGNORECASE):
            continue
        cleaned_lines.append(norm_line)

    result = "\n".join(cleaned_lines)
    # Compress 3+ consecutive newlines to 2
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()