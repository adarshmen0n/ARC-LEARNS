from fastapi import APIRouter
from pydantic import BaseModel
import json

from app.services.vector_store import search
from app.services.ai_manager import ask_ai


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

def clean_json_response(answer):

    if not answer:

        return ""

    answer = answer.strip()

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    if "```json" in answer:

        answer = answer.replace(
            "```json",
            ""
        )

    if "```" in answer:

        answer = answer.replace(
            "```",
            ""
        )

    answer = answer.strip()

    # --------------------------------------------------------
    # Find JSON object
    # --------------------------------------------------------

    start = answer.find("{")
    end = answer.rfind("}")

    if start != -1 and end != -1:

        answer = answer[
            start:end + 1
        ]

    return answer.strip()


# ============================================================
# VALIDATE QUIZ
# ============================================================

def validate_quiz(
    quiz,
    expected_count
):

    valid_questions = []

    if not isinstance(quiz, list):

        return valid_questions


    for item in quiz:

        # ----------------------------------------------------
        # Check object
        # ----------------------------------------------------

        if not isinstance(item, dict):

            continue


        question = item.get(
            "question"
        )

        options = item.get(
            "options"
        )

        correct_answer = item.get(
            "correct_answer"
        )

        explanation = item.get(
            "explanation",
            ""
        )


        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        if not question:

            continue


        # ----------------------------------------------------
        # Validate options
        # ----------------------------------------------------

        if not isinstance(
            options,
            list
        ):

            continue


        if len(options) != 4:

            continue


        # ----------------------------------------------------
        # Validate correct answer
        # ----------------------------------------------------

        if not correct_answer:

            continue


        if correct_answer not in options:

            continue


        # ----------------------------------------------------
        # Create clean question
        # ----------------------------------------------------

        clean_question = {

            "question":
                str(question),

            "options": [
                str(option)
                for option in options
            ],

            "correct_answer":
                str(correct_answer),

            "explanation":
                str(explanation)

        }


        valid_questions.append(
            clean_question
        )


        # ----------------------------------------------------
        # Stop at requested count
        # ----------------------------------------------------

        if len(valid_questions) >= expected_count:

            break


    return valid_questions


# ============================================================
# CREATE QUIZ PROMPT
# ============================================================

def build_quiz_prompt(
    topic,
    number_of_questions,
    context
):

    prompt = f"""
You are ARC LEARNS AI Quiz Generator.

Create a multiple-choice quiz for a student.

TOPIC:
{topic}

NUMBER OF QUESTIONS:
{number_of_questions}

STUDY MATERIAL:
{context}

IMPORTANT RULES:

1. Create exactly {number_of_questions} questions.

2. Every question must have exactly four options.

3. Only one option can be correct.

4. The correct_answer must exactly match
   one of the four options.

5. Every question must be based ONLY
   on the study material.

6. Do not use outside knowledge.

7. Do not invent facts.

8. Avoid duplicate questions.

9. Keep explanations short.

10. Make the questions educational
    and suitable for a student.

11. Return ONLY JSON.

12. Do NOT write anything before the JSON.

13. Do NOT write anything after the JSON.

14. Do NOT use markdown.

15. Do NOT use ```json.

YOUR RESPONSE MUST LOOK EXACTLY LIKE THIS:

{{
    "topic": "{topic}",
    "quiz": [
        {{
            "question": "Example question?",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_answer": "Option A",
            "explanation": "Short explanation."
        }}
    ]
}}

Now generate the quiz.
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
    # ASK AI
    # ========================================================

    answer = ask_ai(
        context,
        prompt,
        use_web_search=False
    )


    # ========================================================
    # CLEAN AI RESPONSE
    # ========================================================

    answer = clean_json_response(
        answer
    )


    # ========================================================
    # DEBUG OUTPUT
    # ========================================================

    print(
        "[QUIZ] AI response:"
    )

    print(answer)


    # ========================================================
    # PARSE JSON
    # ========================================================

    try:

        quiz_data = json.loads(
            answer
        )

    except json.JSONDecodeError as error:

        print(
            "[QUIZ] Invalid JSON returned by AI"
        )

        print(
            "[QUIZ] JSON error:",
            error
        )

        print(
            "[QUIZ] Raw response:"
        )

        print(answer)


        return {

            "topic":
                data.topic,

            "number_of_questions":
                number_of_questions,

            "quiz":
                [],

            "error":
                "AI returned invalid JSON.",

            "raw_response":
                answer,

            "source_chunks":
                results

        }


    # ========================================================
    # GET QUIZ
    # ========================================================

    quiz = quiz_data.get(
        "quiz",
        []
    )


    # ========================================================
    # VALIDATE QUIZ
    # ========================================================

    quiz = validate_quiz(
        quiz,
        number_of_questions
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "topic":
            data.topic,

        "number_of_questions":
            number_of_questions,

        "quiz":
            quiz,

        "source_chunks":
            results

    }