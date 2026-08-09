import re


def clean_text(text: str):

    text = text.replace("\n", " ")

    text = text.replace("\t", " ")

    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text