import json
import logging
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.vector_store import search
from app.services.ai_manager import ask_ai
from app.services.pedagogical_fallback import generate_fallback_quiz

logger = logging.getLogger("arc_learns.quiz")
router = APIRouter()


# ============================================================
# REQUEST MODEL
# ============================================================

class QuizRequest(BaseModel):

    topic: str
    number_of_questions: int = 5


# ============================================================
# PREPARE STUDY CONTEXT
# ============================================================

def prepare_context(results):

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

    # Prevent extremely large prompts
    MAX_CONTEXT_CHARS = 14000

    if len(context) > MAX_CONTEXT_CHARS:

        context = context[:MAX_CONTEXT_CHARS]

    return context


# ============================================================
# EXTRACT JSON FROM AI RESPONSE
# ============================================================

def clean_json_response(answer: str) -> str:

    if not answer:
        return ""

    text = answer.strip()

    # Remove markdown code fences
    if "```json" in text:
        text = text.replace("```json", "")
    if "```" in text:
        text = text.replace("```", "")

    text = text.strip()

    # If already a JSON array, wrap it in a dict
    array_start = text.find("[")
    array_end = text.rfind("]")
    obj_start = text.find("{")
    obj_end = text.rfind("}")

    if obj_start != -1 and obj_end != -1 and (array_start == -1 or obj_start < array_start):
        text = text[obj_start:obj_end + 1]
    elif array_start != -1 and array_end != -1:
        text = '{"quiz": ' + text[array_start:array_end + 1] + '}'

    return text.strip()


# ============================================================
# VALIDATE QUIZ
# ============================================================

def validate_quiz(
    quiz,
    expected_count: int
):

    valid_questions = []

    if not isinstance(quiz, list):
        return valid_questions

    for item in quiz:
        if not isinstance(item, dict):
            continue

        question = item.get("question")
        options = item.get("options")
        correct_answer = item.get("correct_answer")
        explanation = item.get("explanation", "")
        distractor_analysis = item.get("distractor_analysis", {})
        difficulty = item.get("difficulty", "medium").lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        concept_tested = item.get("concept_tested", "")

        if not question or not isinstance(options, list) or len(options) != 4:
            continue

        if not correct_answer or correct_answer not in options:
            # Check if correct_answer matches an option with whitespace stripped
            matched = False
            for opt in options:
                if str(opt).strip().lower() == str(correct_answer).strip().lower():
                    correct_answer = str(opt)
                    matched = True
                    break
            if not matched:
                continue

        # Format distractor analysis into a clean dict if present
        cleaned_distractors = {}
        if isinstance(distractor_analysis, dict):
            for k, v in distractor_analysis.items():
                cleaned_distractors[str(k)] = str(v)

        clean_question = {
            "question": str(question).strip(),
            "options": [str(option).strip() for option in options],
            "correct_answer": str(correct_answer).strip(),
            "explanation": str(explanation).strip(),
            "distractor_analysis": cleaned_distractors,
            "difficulty": difficulty,
            "concept_tested": str(concept_tested).strip()
        }

        valid_questions.append(clean_question)

        if len(valid_questions) >= expected_count:
            break

    return valid_questions


# ============================================================
# CREATE QUIZ PROMPT (PEDAGOGICAL ASSESSMENT ENGINE)
# ============================================================

def build_quiz_prompt(
    topic: str,
    number_of_questions: int,
    context: str
) -> str:

    prompt = f"""You are the ARC LEARN AI Quiz Engine.

Create an interactive educational multiple-choice quiz based strictly on the study material below.

TOPIC:
{topic}

NUMBER OF QUESTIONS:
{number_of_questions}

STUDY MATERIAL:
{context}

PEDAGOGICAL REQUIREMENTS:
1. Create exactly {number_of_questions} distinct multiple-choice questions.
2. Focus on conceptual understanding, mechanism reasoning, and problem solving, NOT superficial trivia.
3. Include a balanced mix of difficulty levels: easy (foundational definition/concept), medium (application/mechanism), and hard (edge case, scenario, or analytical deduction).
4. Each question must have exactly 4 distinct and plausible options. Avoid "All of the above" or "None of the above".
5. The `correct_answer` must match one of the four options identically.
6. `explanation`: Provide a thorough pedagogical explanation (2-3 sentences) explaining WHY the correct option is true and the core principle behind it.
7. `distractor_analysis`: Provide a 1-sentence reason for why each of the 3 incorrect options is wrong or misleading.
8. `difficulty`: One of "easy", "medium", or "hard".
9. `concept_tested`: Short 2-5 word label of the specific sub-concept tested.
10. Strict Grounding: Base questions ONLY on the provided study material. Do not hallucinate facts.

OUTPUT FORMAT:
Output MUST be raw, valid JSON only. Do not include markdown codeblocks or conversational filler.
Format:
{{
    "topic": "{topic}",
    "quiz": [
        {{
            "question": "Clear conceptual question?",
            "options": [
                "Option A text",
                "Option B text",
                "Option C text",
                "Option D text"
            ],
            "correct_answer": "Option A text",
            "explanation": "Clear explanation of why Option A is correct according to the study material.",
            "distractor_analysis": {{
                "Option B text": "Why this option is incorrect",
                "Option C text": "Why this option is incorrect",
                "Option D text": "Why this option is incorrect"
            }},
            "difficulty": "medium",
            "concept_tested": "Concept Name"
        }}
    ]
}}
"""

    return prompt


# ============================================================
# GENERATE QUIZ
# ============================================================

@router.post("/quiz")
def generate_quiz(
    data: QuizRequest
):

    # ========================================================
    # VALIDATE QUESTION COUNT
    # ========================================================

    number_of_questions = max(
        1,
        min(
            data.number_of_questions,
            50
        )
    )


    # ========================================================
    # SEARCH STUDY MATERIAL
    # ========================================================

    results = search(
        data.topic
    )


    if not results:

        return {

            "topic":
                data.topic,

            "number_of_questions":
                number_of_questions,

            "quiz":
                [],

            "message":
                (
                    "I couldn't find enough "
                    "information in the uploaded "
                    "study material."
                )

        }


    # ========================================================
    # PREPARE CONTEXT
    # ========================================================

    context = prepare_context(
        results
    )


    # ========================================================
    # CREATE PROMPT
    # ========================================================

    prompt = build_quiz_prompt(
        data.topic,
        number_of_questions,
        context
    )


    # ========================================================
    # ASK AI WITH RESILIENT FALLBACK
    # ========================================================

    quiz = []

    try:
        answer = ask_ai(
            "",
            prompt,
            use_web_search=False,
            max_tokens=2500
        )
        answer = clean_json_response(answer)
        logger.debug("[QUIZ] Cleaned AI response length: %d", len(answer))
        quiz_data = json.loads(answer)
        quiz = validate_quiz(
            quiz_data.get("quiz", []),
            number_of_questions
        )
    except Exception as error:
        logger.warning("[QUIZ] AI quiz generation failed (%s). Synthesizing grounded quiz directly from study material.", error)

    # If AI returned malformed JSON or empty quiz, synthesize grounded questions
    if not quiz:
        quiz = generate_fallback_quiz(
            data.topic,
            number_of_questions,
            results
        )

    return {
        "topic": data.topic,
        "number_of_questions": len(quiz),
        "quiz": quiz,
        "source_chunks": results
    }