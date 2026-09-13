import logging
from typing import Dict, List, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import (
    ask_ai,
    ask_ai_stream
)
from app.services.pedagogical_fallback import generate_fallback_doubt

logger = logging.getLogger("arc_learns.chat")
router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: Optional[List[ChatMessage]] = None


# ============================================================
# HELPER: BUILD DOUBT CLEARING PROMPT
# ============================================================

def build_doubt_prompt(question: str, context: str) -> str:
    return f"""You are the ARC LEARN AI Tutor. A student is asking a specific doubt about their uploaded study material.

STUDY MATERIAL:
{context}

STUDENT'S QUESTION / DOUBT:
{question}

INSTRUCTIONS:
1. Provide a direct, crystal-clear answer in the first 1-2 sentences.
2. Ground your explanation in the study material provided above.
3. If relevant, provide a concise worked example, code snippet, or formula derivation to clarify the concept.
4. If the student is asking about something not covered in their material, clarify that gently while still providing accurate conceptual guidance.
5. Highlight any common student traps or edge cases related to this question.
6. Keep the tone patient, encouraging, and academically rigorous. Format cleanly with Markdown.
"""


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

    # Retrieve uploaded study material
    results = search(question)
    context = "\n\n---\n\n".join(str(r) for r in results[:6] if r)

    formatted_prompt = build_doubt_prompt(question, context)
    history_payload = [m.model_dump() for m in data.history] if data.history else None

    try:
        answer = ask_ai(
            "",
            formatted_prompt,
            use_web_search=False,
            history=history_payload,
            max_tokens=2000
        )
    except Exception as e:
        logger.warning("Cloud AI unavailable for chat (%s), generating grounded doubt resolution.", e)
        answer = generate_fallback_doubt(question, results)

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
            iter(["Please enter a question."]),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    # Retrieve study material
    results = search(question)
    context = "\n\n---\n\n".join(str(r) for r in results[:6] if r)

    formatted_prompt = build_doubt_prompt(question, context)
    history_payload = [m.model_dump() for m in data.history] if data.history else None

    def stream_with_fallback():
        try:
            tokens_count = 0
            for chunk in ask_ai_stream(
                "",
                formatted_prompt,
                use_web_search=False,
                history=history_payload,
                max_tokens=2000
            ):
                tokens_count += 1
                yield chunk
        except Exception as e:
            logger.warning("Chat stream error (%s), yielding grounded doubt resolution.", e)
            if tokens_count == 0:
                yield generate_fallback_doubt(question, results)

    return StreamingResponse(
        stream_with_fallback(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )