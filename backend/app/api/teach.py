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
# Request model
# ============================================================

class TeachRequest(BaseModel):

    topic: str
    length: str = "medium"


# ============================================================
# Build teaching prompt
# ============================================================

def build_teach_prompt(topic, length, context):

    # --------------------------------------------------------
    # Length instructions
    # --------------------------------------------------------

    if length == "short":

        length_instruction = """
Create a SHORT lesson.

Keep it concise.
Explain only the most important concepts.
Use short paragraphs and a few bullet points.
Do not over-explain.
"""


    elif length == "long":

        length_instruction = """
Create a LONG lesson.

Explain the important concepts thoroughly.
Cover the topic step by step.
Include useful relationships and examples only when
supported by the study material.
Do not repeat the same idea unnecessarily.
"""


    else:

        length_instruction = """
Create a MEDIUM lesson.

Give a balanced explanation.
Cover the important concepts clearly.
Do not make the answer unnecessarily long.
"""


    # --------------------------------------------------------
    # Main prompt
    # --------------------------------------------------------

    prompt = f"""
You are ARC LEARNS, an AI Teacher.

Teach the student using ONLY the study material below.

Topic:
{topic}

Length:
{length.upper()}

Study Material:
{context}

{length_instruction}

Use this structure:

# Introduction
Briefly explain the topic.

# Core Concept
Explain the main ideas.

# Detailed Explanation
Explain the topic according to the requested length.

# Simple Example
Give an example only if supported by the study material.

# Important Points
List the key points.

# Quick Revision
Give a short revision summary.

Rules:
- Use ONLY the study material.
- Do not invent facts.
- Do not add unrelated information.
- Use simple student-friendly language.
- Avoid unnecessary repetition.
- Follow the requested length.
- Short = concise.
- Medium = balanced.
- Long = detailed.
"""


    return prompt


# ============================================================
# Validate length
# ============================================================

def validate_length(value):

    allowed_lengths = [
        "short",
        "medium",
        "long"
    ]

    length = value.lower().strip()

    if length not in allowed_lengths:

        length = "medium"

    return length


# ============================================================
# Prepare context
# ============================================================

def prepare_context(results):

    # --------------------------------------------------------
    # Use the most relevant retrieved chunks.
    # --------------------------------------------------------

    useful_results = results[:5]


    context_parts = []


    for result in useful_results:

        if result:

            context_parts.append(
                str(result)
            )


    context = "\n\n".join(
        context_parts
    )


    # --------------------------------------------------------
    # Safety limit.
    #
    # Prevent unnecessarily huge prompts from slowing down
    # the model.
    # --------------------------------------------------------

    MAX_CONTEXT_CHARS = 16000


    if len(context) > MAX_CONTEXT_CHARS:

        context = context[
            :MAX_CONTEXT_CHARS
        ]


    return context


# ============================================================
# NORMAL / NON-STREAMING TEACH
# ============================================================

@router.post("/teach")
def teach_topic(data: TeachRequest):

    # --------------------------------------------------------
    # Validate length
    # --------------------------------------------------------

    length = validate_length(
        data.length
    )


    # --------------------------------------------------------
    # Search uploaded study material
    # --------------------------------------------------------

    results = search(
        data.topic
    )


    if not results:

        return {

            "topic": data.topic,

            "length": length,

            "lesson": (
                "I couldn't find enough information "
                "about this topic in the uploaded "
                "study material."
            ),

            "source_chunks": []

        }


    # --------------------------------------------------------
    # Prepare relevant context
    # --------------------------------------------------------

    context = prepare_context(
        results
    )


    # --------------------------------------------------------
    # Build compact prompt
    # --------------------------------------------------------

    prompt = build_teach_prompt(
        data.topic,
        length,
        context
    )


    # --------------------------------------------------------
    # Generate lesson
    #
    # Web search is OFF here.
    # Teacher remains grounded in uploaded material.
    # --------------------------------------------------------

    lesson = ask_ai(
        "",
        prompt,
        use_web_search=False
    )


    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {

        "topic": data.topic,

        "length": length,

        "lesson": lesson,

        "source_chunks": results

    }


# ============================================================
# STREAMING TEACH
# ============================================================

@router.post("/teach/stream")
def teach_topic_stream(
    data: TeachRequest
):

    # --------------------------------------------------------
    # Validate length
    # --------------------------------------------------------

    length = validate_length(
        data.length
    )


    # --------------------------------------------------------
    # Search uploaded study material
    # --------------------------------------------------------

    results = search(
        data.topic
    )


    if not results:

        message = (
            "I couldn't find enough information "
            "about this topic in the uploaded "
            "study material."
        )


        return StreamingResponse(

            iter([
                message
            ]),

            media_type="text/plain"

        )


    # --------------------------------------------------------
    # Prepare context
    # --------------------------------------------------------

    context = prepare_context(
        results
    )


    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    prompt = build_teach_prompt(
        data.topic,
        length,
        context
    )


    # --------------------------------------------------------
    # Start streaming
    # --------------------------------------------------------

    stream = ask_ai_stream(

        "",
        prompt,

        use_web_search=False

    )


    # --------------------------------------------------------
    # Return streaming response
    # --------------------------------------------------------

    return StreamingResponse(

        stream,

        media_type="text/plain",

        headers={

            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no"

        }

    )