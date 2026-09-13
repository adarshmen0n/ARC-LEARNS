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
    response_format=None,
    history=None,
    max_tokens=2500
):

    return ask_openrouter(
        context,
        question,
        use_web_search=use_web_search,
        response_format=response_format,
        history=history,
        max_tokens=max_tokens
    )


# ============================================================
# STREAMING AI REQUEST
# ============================================================

def ask_ai_stream(
    context,
    question,
    use_web_search=False,
    history=None,
    max_tokens=2500
):

    return ask_openrouter_stream(
        context,
        question,
        use_web_search=use_web_search,
        history=history,
        max_tokens=max_tokens
    )