import re


def detect_chapters(text: str):

    pattern = r"(Chapter\s+\d+.*?)(?=Chapter\s+\d+|$)"

    chapters = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if chapters:
        return chapters

    return [text]