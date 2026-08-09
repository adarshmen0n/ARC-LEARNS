from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import (
    ask_ai,
    ask_ai_stream
)

router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):
    question: str


# ============================================================
# NORMAL CHAT
# ============================================================

@router.post("/chat")
def chat(data: ChatRequest):

    question = data.question.strip()

    if not question:
        return {
            "question": "",
            "answer": "Please enter a question.",
            "source_chunks": []
        }

    # --------------------------------------------------------
    # Retrieve uploaded study material
    # --------------------------------------------------------

    results = search(question)

    context = "\n\n".join(results[:5])

    # --------------------------------------------------------
    # Ask AI
    #
    # Web search OFF.
    # This chat is based on uploaded material.
    # --------------------------------------------------------

    answer = ask_ai(
        context,
        question,
        use_web_search=False
    )

    return {
        "question": question,
        "answer": answer,
        "source_chunks": results
    }


# ============================================================
# STREAMING CHAT
# ============================================================

@router.post("/chat/stream")
def chat_stream(data: ChatRequest):

    question = data.question.strip()

    if not question:

        return StreamingResponse(
            iter([
                "Please enter a question."
            ]),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    # --------------------------------------------------------
    # Retrieve study material
    # --------------------------------------------------------

    results = search(question)

    context = "\n\n".join(results[:5])

    # --------------------------------------------------------
    # Start AI streaming
    #
    # IMPORTANT:
    # Web search is OFF.
    # --------------------------------------------------------

    stream = ask_ai_stream(
        context,
        question,
        use_web_search=False
    )

    # --------------------------------------------------------
    # Return chunks immediately
    # --------------------------------------------------------

    return StreamingResponse(
        stream,
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )