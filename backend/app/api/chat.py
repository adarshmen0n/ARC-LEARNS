from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import (
    ask_ai,
    ask_ai_stream
)


router = APIRouter()


class ChatRequest(BaseModel):

    question: str


# ============================================================
# NORMAL ASK AI
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
    # Search uploaded study material
    # --------------------------------------------------------

    results = search(question)


    context = "\n\n".join(results)


    # --------------------------------------------------------
    # Ask AI
    #
    # Web search is enabled.
    # The AI can use it when current information is needed.
    # --------------------------------------------------------

    answer = ask_ai(
        context,
        question,
        use_web_search=True
    )


    return {
        "question": question,
        "answer": answer,
        "source_chunks": results
    }


# ============================================================
# STREAMING ASK AI
# ============================================================

@router.post("/chat/stream")
def chat_stream(data: ChatRequest):

    question = data.question.strip()


    if not question:

        return StreamingResponse(

            iter([
                "Please enter a question."
            ]),

            media_type="text/plain"
        )


    # --------------------------------------------------------
    # Search uploaded study material
    # --------------------------------------------------------

    results = search(question)


    context = "\n\n".join(results)


    # --------------------------------------------------------
    # Streaming AI response
    #
    # Web search is enabled.
    # --------------------------------------------------------

    stream = ask_ai_stream(
        context,
        question,
        use_web_search=True
    )


    return StreamingResponse(

        stream,

        media_type="text/plain",

        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )