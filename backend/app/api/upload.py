from fastapi import APIRouter, UploadFile, File
import os

from app.services.document_loader import extract_text
from app.services.text_cleaner import clean_text
from app.services.chapter_detector import detect_chapters
from app.services.chunker import create_chunks
from app.services.vector_store import create_vector_store


router = APIRouter()


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    # Supported file types
    allowed_extensions = [
        ".pdf",
        ".docx",
        ".txt",
        ".csv"
    ]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:

        return {
            "filename": file.filename,
            "message": "Unsupported file type.",
            "supported_formats": [
                "PDF",
                "DOCX",
                "TXT",
                "CSV"
            ]
        }

    # Create upload directory
    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join(
        "uploads",
        file.filename
    )

    # Save uploaded file
    file_content = await file.read()

    with open(file_path, "wb") as f:
        f.write(file_content)

    # Extract text
    try:

        text = extract_text(file_path)

    except Exception as e:

        return {
            "filename": file.filename,
            "message": "Could not read the uploaded file.",
            "error": str(e)
        }

    # Check extracted text
    if not text.strip():

        return {
            "filename": file.filename,
            "message": "No readable text was found in the file."
        }

    # Clean text
    cleaned_text = clean_text(text)

    # Detect chapters
    chapters = detect_chapters(cleaned_text)

    # Create chunks
    chunks = create_chunks(cleaned_text)

    # Create FAISS vector store
    create_vector_store(chunks)

    # Chapter titles
    chapter_titles = []

    for i, chapter in enumerate(chapters):

        first_line = chapter.split("\n")[0].strip()

        if first_line == "":
            first_line = f"Chapter {i + 1}"

        chapter_titles.append(first_line)

    return {
        "filename": file.filename,
        "file_type": extension,
        "chapters_found": len(chapters),
        "total_chunks": len(chunks),
        "chapter_titles": chapter_titles,
        "vector_database": "Created Successfully",
        "first_chunk": chunks[0] if chunks else "",
        "message": "File is now ready for AI Search"
    }