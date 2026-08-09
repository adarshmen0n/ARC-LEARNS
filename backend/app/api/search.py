from fastapi import APIRouter
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import ask_ai

router = APIRouter()


class SearchRequest(BaseModel):
    question: str


@router.post("/search")
def search_pdf(data: SearchRequest):

    results = search(data.question)

    if not results:
        return {
            "question": data.question,
            "answer": "I couldn't find the answer in the uploaded PDF.",
            "source_chunks": []
        }

    context = "\n\n".join(results)

    answer = ask_ai(
        context,
        data.question
    )

    return {
        "question": data.question,
        "answer": answer,
        "source_chunks": results
    }