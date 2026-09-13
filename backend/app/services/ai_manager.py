"""Multi-Provider AI Orchestration Engine for ARC LEARN.

Orchestrates a 4-tier resilient waterfall:
1. Tier 1 (Primary): Google Gemini API (1,500 requests/day, 1M token window)
2. Tier 2 (Secondary): GroqCloud LPUs (World's fastest inference: 300-500 tok/s)
3. Tier 3 (Tertiary): OpenRouter Multi-Model Rotation
4. Tier 4 (Offline Fallback): Grounded Pedagogical Fallback Engine (pedagogical_fallback.py)

Guarantees 100% uptime with zero single points of failure.
"""

import logging
from typing import Any, Dict, Generator, List, Optional

from .gemini_service import call_gemini, call_gemini_stream, get_gemini_key
from .groq_service import call_groq, call_groq_stream, get_groq_key
from .openrouter_service import (
    ask_openrouter,
    ask_openrouter_stream,
    get_openrouter_key,
)

logger = logging.getLogger("arc_learns.ai_manager")


def build_unified_messages(
    context: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_role: str = "You are ARC LEARN, an expert, patient, and deeply knowledgeable personal AI Teacher.",
) -> List[Dict[str, str]]:
    """Construct standard messages payload for any LLM provider."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": system_role}
    ]

    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    if context:
        user_content = f"""Use the study material provided below to answer clearly and accurately.

STUDY MATERIAL:
{context}

QUESTION / REQUEST:
{question}
"""
    else:
        user_content = question

    messages.append({"role": "user", "content": user_content})
    return messages


def get_provider_status() -> Dict[str, Any]:
    """Report active and available AI providers."""
    has_gemini = bool(get_gemini_key())
    has_groq = bool(get_groq_key())
    has_openrouter = bool(get_openrouter_key())

    primary = "gemini" if has_gemini else ("groq" if has_groq else ("openrouter" if has_openrouter else "grounded_fallback"))
    return {
        "gemini": has_gemini,
        "groq": has_groq,
        "openrouter": has_openrouter,
        "grounded_fallback": True,
        "active_primary": primary,
    }


# ============================================================
# UNIFIED NON-STREAMING AI REQUEST
# ============================================================

def ask_ai(
    context: str,
    question: str,
    use_web_search: bool = False,
    response_format: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> str:
    """Execute non-streaming request through Tier 1 -> Tier 2 -> Tier 3 -> Tier 4."""
    messages = build_unified_messages(context, question, history)
    last_error: Optional[Exception] = None

    # Tier 1: Google Gemini API
    if get_gemini_key():
        try:
            return call_gemini(messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            logger.warning("Tier 1 (Gemini) failed (%s), falling over to Tier 2 (Groq)...", e)

    # Tier 2: Groq API
    if get_groq_key():
        try:
            return call_groq(messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            logger.warning("Tier 2 (Groq) failed (%s), falling over to Tier 3 (OpenRouter)...", e)

    # Tier 3: OpenRouter API
    if get_openrouter_key():
        try:
            return ask_openrouter(
                context,
                question,
                use_web_search=use_web_search,
                response_format=response_format,
                history=history,
                max_tokens=max_tokens,
            )
        except Exception as e:
            last_error = e
            logger.warning("Tier 3 (OpenRouter) failed (%s), falling over to Tier 4 (Offline Fallback)...", e)

    raise RuntimeError(f"All cloud AI providers exhausted. Last error: {last_error}")


# ============================================================
# UNIFIED STREAMING AI REQUEST
# ============================================================

def ask_ai_stream(
    context: str,
    question: str,
    use_web_search: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> Generator[str, None, None]:
    """Execute streaming request through Tier 1 -> Tier 2 -> Tier 3 -> Tier 4."""
    messages = build_unified_messages(context, question, history)
    last_error: Optional[Exception] = None

    # Tier 1: Google Gemini API
    if get_gemini_key():
        try:
            yielded = False
            for chunk in call_gemini_stream(messages, max_tokens=max_tokens):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("Tier 1 (Gemini Stream) failed (%s), trying Tier 2 (Groq)...", e)

    # Tier 2: Groq API
    if get_groq_key():
        try:
            yielded = False
            for chunk in call_groq_stream(messages, max_tokens=max_tokens):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("Tier 2 (Groq Stream) failed (%s), trying Tier 3 (OpenRouter)...", e)

    # Tier 3: OpenRouter API
    if get_openrouter_key():
        try:
            yielded = False
            for chunk in ask_openrouter_stream(
                context,
                question,
                use_web_search=use_web_search,
                history=history,
                max_tokens=max_tokens,
            ):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("Tier 3 (OpenRouter Stream) failed (%s), cascading to Tier 4...", e)

    raise RuntimeError(f"All cloud AI stream providers exhausted. Last error: {last_error}")


# ============================================================
# ARC ZERO UNIVERSAL INTELLIGENCE
# ============================================================

def ask_arc0(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> str:
    """Universal general intelligence query through Multi-Provider waterfall."""
    system_role = (
        "You are ARC ZERO, an autonomous general artificial intelligence assistant "
        "designed for deep technical analysis, programming, mathematics, and complex reasoning."
    )
    messages = build_unified_messages("", question, history, system_role=system_role)
    last_error: Optional[Exception] = None

    # Tier 1: Gemini
    if get_gemini_key():
        try:
            return call_gemini(messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Tier 1 (Gemini) failed (%s)...", e)

    # Tier 2: Groq
    if get_groq_key():
        try:
            return call_groq(messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Tier 2 (Groq) failed (%s)...", e)

    # Tier 3: OpenRouter
    if get_openrouter_key():
        try:
            from .openrouter_service import call_llm_with_fallback
            return call_llm_with_fallback(messages, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Tier 3 (OpenRouter) failed (%s)...", e)

    return (
        "**ARC Zero Status Notice:**\n\n"
        f"All configured cloud AI endpoints are currently exhausted or rate-limited ({last_error}). "
        "Please provide a `GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY` in environment variables."
    )


def ask_arc0_stream(
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> Generator[str, None, None]:
    """Streaming ARC Zero intelligence through Multi-Provider waterfall."""
    system_role = (
        "You are ARC ZERO, an autonomous general artificial intelligence assistant "
        "designed for deep technical analysis, programming, mathematics, and complex reasoning."
    )
    messages = build_unified_messages("", question, history, system_role=system_role)
    last_error: Optional[Exception] = None

    # Tier 1: Gemini
    if get_gemini_key():
        try:
            yielded = False
            for chunk in call_gemini_stream(messages, max_tokens=max_tokens):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Stream Tier 1 (Gemini) failed (%s)...", e)

    # Tier 2: Groq
    if get_groq_key():
        try:
            yielded = False
            for chunk in call_groq_stream(messages, max_tokens=max_tokens):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Stream Tier 2 (Groq) failed (%s)...", e)

    # Tier 3: OpenRouter
    if get_openrouter_key():
        try:
            from .openrouter_service import call_llm_stream_with_fallback
            yielded = False
            for chunk in call_llm_stream_with_fallback(messages, max_tokens=max_tokens):
                yielded = True
                yield chunk
            if yielded:
                return
        except Exception as e:
            last_error = e
            logger.warning("ARC0 Stream Tier 3 (OpenRouter) failed (%s)...", e)

    raise RuntimeError(f"All ARC0 streaming providers exhausted: {last_error}")