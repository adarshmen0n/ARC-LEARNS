from typing import Dict, List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.openrouter_service import (
    ask_arc0,
    ask_arc0_stream
)


router = APIRouter()


class ARC0Message(BaseModel):
    role: str
    content: str


class ARC0Request(BaseModel):
    question: str
    history: Optional[List[ARC0Message]] = None


# ============================================================
# NORMAL ARC 0 ENDPOINT
# ============================================================

@router.post("/arc0")
def arc0_chat(data: ARC0Request):

    question = data.question.strip()

    if not question:
        return {
            "question": "",
            "answer": "Please enter a question."
        }

    try:
        answer = ask_arc0(
            question,
            history=history_payload
        )
    except Exception as e:
        answer = (
            "**ARC Zero Status Notice:**\n\n"
            "The configured OpenRouter API key has reached its daily free-tier request limit (HTTP 429). "
            "Please update `OPENROUTER_API_KEY` in `backend/.env` or add credits to unlock unlimited queries."
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
            iter(["Please enter a question."]),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    history_payload = [m.model_dump() for m in data.history] if data.history else None

    def safe_arc0_stream():
        try:
            tokens_count = 0
            for chunk in ask_arc0_stream(
                question,
                history=history_payload
            ):
                tokens_count += 1
                yield chunk
        except Exception:
            if tokens_count == 0:
                yield (
                    "**ARC Zero Status Notice:**\n\n"
                    "The configured OpenRouter API key has reached its daily free-tier request limit (HTTP 429). "
                    "Please update `OPENROUTER_API_KEY` in `backend/.env` or add credits to unlock unlimited queries."
                )

    return StreamingResponse(
        safe_arc0_stream(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )