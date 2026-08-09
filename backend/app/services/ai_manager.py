from .openrouter_service import (
    ask_openrouter,
    ask_openrouter_stream
)


# ============================================================
# NORMAL AI REQUEST
# ============================================================

def ask_ai(
    context,
    question,
    use_web_search=False,
    response_format=None
):

    return ask_openrouter(
        context,
        question,
        use_web_search=use_web_search,
        response_format=response_format
    )


# ============================================================
# STREAMING AI REQUEST
# ============================================================

def ask_ai_stream(
    context,
    question,
    use_web_search=False
):

    return ask_openrouter_stream(
        context,
        question,
        use_web_search=use_web_search
    )