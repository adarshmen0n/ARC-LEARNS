import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import (
    ask_ai,
    ask_ai_stream
)
from app.services.pedagogical_fallback import generate_fallback_lesson

logger = logging.getLogger("arc_learns.teach")
router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class TeachRequest(BaseModel):

    topic: str
    length: str = "medium"


# ============================================================
# VALIDATE LENGTH
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
# PREPARE CONTEXT
# ============================================================

def prepare_context(results):

    useful_results = results[:8]

    context_parts = []

    for result in useful_results:

        if result:
            context_parts.append(
                str(result)
            )

    context = "\n\n---\n\n".join(context_parts)

    MAX_CONTEXT_CHARS = 18000

    if len(context) > MAX_CONTEXT_CHARS:

        context = context[:MAX_CONTEXT_CHARS]

    return context


# ============================================================
# BUILD TEACHING PROMPT (PEDAGOGICAL MASTERCLASS ENGINE)
# ============================================================

def build_teach_prompt(
    topic: str,
    length: str,
    context: str
) -> str:

    if length == "short":
        depth_guide = """
DEPTH LEVEL: FOCUSED / HIGH-YIELD LESSON
- Provide a clear, punchy, high-yield lesson that immediately builds deep comprehension.
- Focus on the core intuition, mechanical essence, a crisp worked example or formula breakdown, the primary pitfall to avoid, and essential memory anchors.
- Thorough and explanatory, never a shallow bullet list.
"""
    elif length == "long":
        depth_guide = """
DEPTH LEVEL: COMPREHENSIVE MASTERCLASS CHAPTER
- Deliver an exhaustive, textbook-grade chapter covering every dimension of the topic found in the study material.
- Break down the theoretical grounding, underlying mechanics, step-by-step mathematical derivations or full code implementations with line-by-line breakdown, edge cases, trade-offs, multiple common student misconceptions, and rigorous practice problems.
- Write in deep, engaging explanatory prose with rich structural organization.
"""
    else:  # medium
        depth_guide = """
DEPTH LEVEL: IN-DEPTH TUTORIAL
- Deliver a comprehensive, well-paced tutorial that guides the student from fundamental intuition to technical mastery.
- Provide clear narrative progression, rigorous conceptual explanation, a complete worked example or code demonstration, common pitfalls, and active-recall questions.
- Balance depth with clarity.
"""

    prompt = f"""You are the ARC LEARN AI Teacher, an elite, patient, and deeply knowledgeable personal educator.

Your mission is to transform the provided study material into an engaging, structured, and deep masterclass lesson for the student.

TOPIC TO TEACH:
{topic}

LESSON DEPTH:
{length.upper()}

STUDY MATERIAL:
{context}

{depth_guide}

PEDAGOGICAL INSTRUCTIONS & STRUCTURE:
Structure your lesson using clear Markdown headings (# and ##), formatted code blocks or mathematical formulations, and callouts:

# 1. Intuition & Mental Model
- Hook the student with an intuitive mental model, real-world analogy, or clear motivation explaining WHY this concept exists and what problem it solves.
- Connect it to fundamental principles before diving into technicalities.

# 2. Formal Concepts & Theoretical Foundation
- Define key terms, core principles, equations, theorems, or data structures with precision.
- Ground your explanation strictly in the provided study material.
- If mathematical or algorithmic, state equations clearly (using standard LaTeX or clean text math).

# 3. Step-by-Step Mechanical Breakdown
- Walk through how this concept or system actually works under the hood.
- Detail the progression: What happens first? What are the inputs, transformations, internal state changes, and outputs?
- If applicable, describe architecture or flow step-by-step.

# 4. Deep Worked Example & Practical Walkthrough
- Provide a concrete, fully worked-out example based on the topic:
  * For Programming/CS: Write clean, runnable code with input/output and a line-by-line walkthrough explaining key operations and time/space complexity.
  * For Math/Physics: Provide a step-by-step numerical calculation or algebraic derivation showing every intermediate step.
  * For Science/Engineering: Detail the step-by-step mechanism or chemical/physical process.
  * For Humanities/Business/Other: Walk through a concrete case study or realistic scenario application.

# 5. Common Misconceptions & Traps
- Address 2 to 3 specific areas where students or practitioners frequently get confused or make errors.
- Clearly explain WHY the misconception is wrong and how to think about it correctly.
- Discuss important edge cases or limitations.

# 6. Key Takeaways & Mental Anchors
- Provide a high-impact summary of the 3-5 core takeaways that the student must remember.
- Provide a memorable rule of thumb or memory anchor.

# 7. Knowledge Check & Reflection
- Provide 2-3 targeted active-recall reflection questions or mini-exercises (with brief answers or hints labeled) so the student can self-evaluate their grasp.

STRICT GROUNDING & TEACHING RULES:
1. Base all factual information strictly on the provided study material. Do NOT invent facts or hallucinate external information not present in the notes.
2. Use engaging, encouraging, and pedagogically sound language. Speak directly to the student ("Notice that...", "Let's examine why...", "A common mistake here is...").
3. DO NOT output lazy 2-line bullet summaries. Deliver a real educational experience with genuine explanatory depth.
4. Format all headings, code blocks (```language), bold text, and lists cleanly in standard Markdown.
"""

    return prompt


# ============================================================
# NORMAL TEACH
# ============================================================

@router.post("/teach")
def teach_topic(data: TeachRequest):

    length = validate_length(
        data.length
    )

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

    context = prepare_context(
        results
    )

    prompt = build_teach_prompt(
        data.topic,
        length,
        context
    )

    try:
        lesson = ask_ai(
            "",
            prompt,
            use_web_search=False
        )
    except Exception as e:
        logger.warning("Cloud AI provider offline/rate-limited (%s). Synthesizing grounded pedagogical lesson.", e)
        lesson = generate_fallback_lesson(data.topic, length, results)

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

    length = validate_length(
        data.length
    )

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
            iter([message]),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    context = prepare_context(
        results
    )

    prompt = build_teach_prompt(
        data.topic,
        length,
        context
    )

    def stream_with_fallback():
        try:
            tokens_count = 0
            for chunk in ask_ai_stream("", prompt, use_web_search=False):
                tokens_count += 1
                yield chunk
        except Exception as e:
            logger.warning("Streaming AI failed (%s), yielding grounded pedagogical lesson.", e)
            if tokens_count == 0:
                fallback_lesson = generate_fallback_lesson(data.topic, length, results)
                yield fallback_lesson

    return StreamingResponse(
        stream_with_fallback(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )