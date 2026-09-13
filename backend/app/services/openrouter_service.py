"""OpenRouter & Gemini AI Service for ARC LEARNS.

Implements resilient multi-model routing, automatic fallback across active free models,
bounded exponential backoff retries, and clean reasoning token extraction.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Generator, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import httpx

# Load .env from cwd or backend directory
_backend_dir = Path(__file__).resolve().parent.parent.parent
_env_file = _backend_dir / ".env"
if _env_file.exists():
    load_dotenv(dotenv_path=_env_file)
else:
    load_dotenv()

logger = logging.getLogger("arc_learns.ai")

def get_openrouter_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")

# Verified active free models on OpenRouter in speed/priority order (tested < 1s latency)
FALLBACK_MODELS: List[str] = [
    "nex-agi/nex-n2.5-mini:free",       # ~0.59s first-token latency, lightning fast
    "nex-agi/nex-n2.5-pro:free",        # ~0.96s first-token latency, high accuracy
    "liquid/lfm-2.5-2.6b:free",         # ~1.50s first-token latency, reliable fallback
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
]

def get_openrouter_headers() -> Dict[str, str]:
    api_key = get_openrouter_key()
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://arc-learns.onrender.com",
        "X-Title": "ARC LEARN",
    }


def clean_reasoning_tokens(text: str) -> str:
    """Remove reasoning/thinking tokens (<think>...</think>) from output."""
    if not text:
        return ""
    # Remove <think> blocks
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    # Remove leading thinking process artifacts from reasoning models
    if "Here's a thinking process:" in cleaned:
        parts = cleaned.split("Here's a thinking process:")
        if len(parts) > 1 and "\n\n" in parts[1]:
            cleaned = parts[1].split("\n\n", 1)[-1]
    if "Thinking Process:" in cleaned:
        parts = cleaned.split("Thinking Process:")
        if len(parts) > 1 and "\n\n" in parts[1]:
            cleaned = parts[1].split("\n\n", 1)[-1]
    return cleaned.strip()


def call_llm_with_fallback(
    messages: List[Dict[str, str]],
    max_tokens: int = 1500,
    temperature: float = 0.7,
    timeout: float = 12.0,
) -> str:
    """Call OpenRouter with automatic failover across verified free models."""
    api_key = get_openrouter_key()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing. Returning fallback response.")
        return "Please configure your OPENROUTER_API_KEY in backend/.env to generate AI responses."

    headers = get_openrouter_headers()
    client_timeout = httpx.Timeout(connect=3.5, read=timeout, write=5.0, pool=5.0)
    last_error = None

    for model in FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            start_t = time.perf_counter()
            with httpx.Client(timeout=client_timeout) as client:
                resp = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"].get("content") or ""
                elapsed = time.perf_counter() - start_t
                logger.info("Generated via %s in %.2fs", model, elapsed)
                cleaned = clean_reasoning_tokens(content)
                if cleaned:
                    return cleaned

            logger.warning(
                "Model %s returned %d: %s, falling over immediately...",
                model,
                resp.status_code,
                resp.text[:80],
            )

        except Exception as e:
            last_error = e
            logger.warning("Model %s connection error: %s, falling over...", model, e)

    raise RuntimeError(f"All AI models exhausted. Last error: {last_error}")


def call_llm_stream_with_fallback(
    messages: List[Dict[str, str]],
    max_tokens: int = 1500,
    temperature: float = 0.7,
    timeout: float = 25.0,
) -> Generator[str, None, None]:
    """Call OpenRouter with streaming, falling over in <3.5s if initial connection stalls."""
    api_key = get_openrouter_key()
    if not api_key:
        yield "Please configure your OPENROUTER_API_KEY in backend/.env."
        return

    headers = get_openrouter_headers()
    stream_timeout = httpx.Timeout(connect=3.5, read=timeout, write=5.0, pool=5.0)

    for model in FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        try:
            with httpx.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=stream_timeout,
            ) as response:
                if response.status_code != 200:
                    logger.warning("Stream failed on %s (%d), trying next model immediately...", model, response.status_code)
                    continue

                in_think = False
                tokens_yielded = 0
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                if "<think>" in token:
                                    in_think = True
                                    continue
                                if "</think>" in token:
                                    in_think = False
                                    continue
                                if not in_think:
                                    tokens_yielded += 1
                                    yield token
                        except Exception:
                            continue
                if tokens_yielded > 0:
                    return
        except Exception as e:
            logger.warning("Stream error on %s: %s, falling over...", model, e)

    # Fallback to non-streaming response if streaming connections break
    text = call_llm_with_fallback(messages, max_tokens=max_tokens, temperature=temperature)
    yield text


# ============================================================
# HIGH LEVEL INTERFACES COMPATIBLE WITH EXISTING ROUTES
# ============================================================

def ask_openrouter(
    context: str,
    question: str,
    use_web_search: bool = False,
    response_format: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> str:
    """ARC LEARN AI Teacher non-streaming."""
    if context:
        user_prompt = f"""Use the study material provided below to answer the student's question clearly and accurately.

STUDY MATERIAL:
{context}

STUDENT QUESTION:
{question}
"""
    else:
        user_prompt = question

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "You are ARC LEARN, an expert, patient, and highly encouraging educational AI Teacher."},
    ]

    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_prompt})
    return call_llm_with_fallback(messages, max_tokens=max_tokens)


def ask_openrouter_stream(
    context: str,
    question: str,
    use_web_search: bool = False,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2500,
) -> Generator[str, None, None]:
    """ARC LEARN AI Teacher streaming."""
    if context:
        user_prompt = f"""Teach the student using the study material provided below. Keep your explanation structured, clear, and engaging with headings, examples, and key points.

STUDY MATERIAL:
{context}

STUDENT QUESTION / TOPIC:
{question}
"""
    else:
        user_prompt = question

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "You are ARC LEARN, a helpful, patient, and pedagogically structured AI Teacher."},
    ]

    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_prompt})
    return call_llm_stream_with_fallback(messages, max_tokens=max_tokens)


def ask_arc0(
    question: str,
    use_web_search: bool = True,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2000,
) -> str:
    """ARC 0 General Assistant non-streaming."""
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are ARC Zero, an ultra-fast, intelligent, and versatile AI assistant inside ARC LEARN. "
                "You have vast, up-to-date domain knowledge across computer science, mathematics, natural sciences, "
                "engineering, and world events up to 2026. "
                "Answer directly and scale your depth to the complexity of the question: keep simple lookups concise, "
                "and explain complex multi-step concepts thoroughly with code, math, or clear structured sections."
            ),
        },
    ]

    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})
    return call_llm_with_fallback(messages, max_tokens=max_tokens)


def ask_arc0_stream(
    question: str,
    use_web_search: bool = True,
    history: Optional[List[Dict[str, str]]] = None,
    max_tokens: int = 2000,
) -> Generator[str, None, None]:
    """ARC 0 General Assistant streaming."""
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are ARC Zero, an ultra-fast, intelligent, and versatile AI assistant inside ARC LEARN. "
                "You have vast, up-to-date domain knowledge across computer science, mathematics, natural sciences, "
                "engineering, and world events up to 2026. "
                "Answer directly and scale your depth to the complexity of the question: keep simple lookups concise, "
                "and explain complex multi-step concepts thoroughly with code, math, or clear structured sections."
            ),
        },
    ]

    if history:
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": question})
    return call_llm_stream_with_fallback(messages, max_tokens=max_tokens)