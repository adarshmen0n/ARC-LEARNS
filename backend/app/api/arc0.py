from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.openrouter_service import (
    ask_arc0,
    ask_arc0_stream
)


router = APIRouter()


class ARC0Request(BaseModel):

    question: str


# ============================================================
# NORMAL ARC 0 ENDPOINT
# Existing endpoint - kept for compatibility
# ============================================================

@router.post("/arc0")
def arc0_chat(data: ARC0Request):

    question = data.question.strip()


    if not question:

        return {
            "answer": "Please enter a question."
        }


    answer = ask_arc0(
        question
    )


    return {
        "question": question,
        "answer": answer
    }


# ============================================================
# STREAMING ARC 0 ENDPOINT
# ============================================================

@router.post("/arc0/stream")
def arc0_chat_stream(data: ARC0Request):

    question = data.question.strip()


    if not question:

        return StreamingResponse(

            iter([
                "Please enter a question."
            ]),

            media_type="text/plain"
        )


    stream = ask_arc0_stream(
        question
    )


    return StreamingResponse(

        stream,

        media_type="text/plain",

        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )