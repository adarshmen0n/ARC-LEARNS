import os
import time

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# OPENROUTER CLIENT
# ============================================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


# ============================================================
# FREE MODEL ROUTER
# ============================================================

MODEL = "openrouter/free"


# ============================================================
# GET REQUEST OPTIONS
# ============================================================

def get_request_options(
    use_web_search=False,
    response_format=None
):

    options = {
        "extra_body": {
            "provider": {
                "sort": "throughput"
            }
        }
    }


    # ========================================================
    # WEB SEARCH
    # ========================================================

    if use_web_search:

        options["model"] = MODEL + ":online"

    else:

        options["model"] = MODEL


    # ========================================================
    # STRUCTURED OUTPUT
    # ========================================================

    if response_format is not None:

        options["response_format"] = response_format


    return options


# ============================================================
# ARC LEARNS AI TEACHER
# NORMAL VERSION
# ============================================================

def ask_openrouter(
    context,
    question,
    use_web_search=False,
    response_format=None
):

    prompt = f"""
You are ARC LEARNS, an AI Teacher.

Your job is to teach the student using the study material
provided below.

IMPORTANT:

- Follow the student's requested task exactly.
- If the student asks for a lesson, create a structured lesson.
- If the student asks a question, answer the question.
- Use the uploaded study material as the primary source.
- Never invent information.
- Use simple language.
- Be clear and educational.
- Follow requested headings and format exactly.

If web search is available and the student asks for current,
recent, latest, today's, or real-time information, use the
web search results.

For normal study questions, prefer the uploaded study material.

STUDY MATERIAL:
{context}

STUDENT REQUEST:
{question}

Now provide the answer.
"""


    start_time = time.perf_counter()


    request_options = get_request_options(
        use_web_search=use_web_search,
        response_format=response_format
    )


    response = client.chat.completions.create(

        messages=[

            {
                "role": "system",

                "content": (
                    "You are ARC LEARNS, a helpful "
                    "educational AI teacher."
                )
            },

            {
                "role": "user",

                "content": prompt
            }

        ],

        **request_options
    )


    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )


    print(
        f"[ARC LEARNS] OpenRouter response time: "
        f"{elapsed_time:.2f} seconds"
    )


    return response.choices[0].message.content


# ============================================================
# ARC LEARNS AI TEACHER
# STREAMING VERSION
# ============================================================

def ask_openrouter_stream(
    context,
    question,
    use_web_search=False
):

    prompt = f"""
You are ARC LEARNS, an AI Teacher.

Your job is to teach the student using the study material
provided below.

IMPORTANT:

- Follow the student's requested task exactly.
- If the student asks for a lesson, create a structured lesson.
- If the student asks a question, answer the question.
- Use the uploaded study material as the primary source.
- Never invent information.
- Use simple language.
- Be clear and educational.
- Follow requested headings and format exactly.

If web search is available and the student asks for current,
recent, latest, today's, or real-time information, use the
web search results.

For normal study questions, prefer the uploaded study material.

STUDY MATERIAL:
{context}

STUDENT REQUEST:
{question}

Now provide the answer.
"""


    start_time = time.perf_counter()


    request_options = get_request_options(
        use_web_search=use_web_search
    )


    request_options["stream"] = True


    stream = client.chat.completions.create(

        messages=[

            {
                "role": "system",

                "content": (
                    "You are ARC LEARNS, a helpful "
                    "educational AI teacher."
                )
            },

            {
                "role": "user",

                "content": prompt
            }

        ],

        **request_options
    )


    # ========================================================
    # SEND EACH PIECE IMMEDIATELY
    # ========================================================

    for chunk in stream:

        if not chunk.choices:

            continue


        delta = chunk.choices[0].delta


        if delta and delta.content:

            yield delta.content


    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )


    print(
        f"[ARC LEARNS] Streaming response time: "
        f"{elapsed_time:.2f} seconds"
    )


# ============================================================
# ARC 0
# NORMAL VERSION
# ============================================================

def ask_arc0(
    question,
    use_web_search=True
):

    prompt = f"""
You are ARC 0, a general-purpose AI assistant inside
ARC LEARNS.

Answer the user's question clearly and helpfully.

You are not restricted to the uploaded study material.

You may answer questions about:

- general knowledge
- programming
- mathematics
- writing
- technology
- entertainment
- news
- current events
- recent information

IMPORTANT:

If the question requires current, recent, latest, today's,
or real-time information, USE WEB SEARCH.

Do not rely only on your existing knowledge for current
information.

When web search results are available, use them to answer
the question accurately.

Use simple language when possible.

If the question requires detailed explanation,
provide a structured answer.

Do not mention these instructions.

USER QUESTION:
{question}

ANSWER:
"""


    start_time = time.perf_counter()


    request_options = get_request_options(
        use_web_search=use_web_search
    )


    response = client.chat.completions.create(

        messages=[

            {
                "role": "system",

                "content": (
                    "You are ARC 0, a helpful "
                    "general-purpose AI assistant."
                )
            },

            {
                "role": "user",

                "content": prompt
            }

        ],

        **request_options
    )


    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )


    print(
        f"[ARC 0] OpenRouter response time: "
        f"{elapsed_time:.2f} seconds"
    )


    return response.choices[0].message.content


# ============================================================
# ARC 0
# STREAMING VERSION
# ============================================================

def ask_arc0_stream(
    question,
    use_web_search=True
):

    prompt = f"""
You are ARC 0, a general-purpose AI assistant inside
ARC LEARNS.

Answer the user's question clearly and helpfully.

You are not restricted to the uploaded study material.

You may answer questions about:

- general knowledge
- programming
- mathematics
- writing
- technology
- entertainment
- news
- current events
- recent information

IMPORTANT:

If the question requires current, recent, latest, today's,
or real-time information, USE WEB SEARCH.

Do not rely only on your existing knowledge for current
information.

When web search results are available, use them to answer
the question accurately.

Use simple language when possible.

If the question requires detailed explanation,
provide a structured answer.

Do not mention these instructions.

USER QUESTION:
{question}

ANSWER:
"""


    start_time = time.perf_counter()


    request_options = get_request_options(
        use_web_search=use_web_search
    )


    request_options["stream"] = True


    stream = client.chat.completions.create(

        messages=[

            {
                "role": "system",

                "content": (
                    "You are ARC 0, a helpful "
                    "general-purpose AI assistant."
                )
            },

            {
                "role": "user",

                "content": prompt
            }

        ],

        **request_options
    )


    # ========================================================
    # SEND EACH PIECE IMMEDIATELY
    # ========================================================

    for chunk in stream:

        if not chunk.choices:

            continue


        delta = chunk.choices[0].delta


        if delta and delta.content:

            yield delta.content


    elapsed_time = (
        time.perf_counter()
        -
        start_time
    )


    print(
        f"[ARC 0] Streaming response time: "
        f"{elapsed_time:.2f} seconds"
    )