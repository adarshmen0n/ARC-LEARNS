from app.services.openrouter_service import ask_openrouter


def ask_gemini(context, question):
    return ask_openrouter(context, question)