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

# Active free models on OpenRouter in priority order
FALLBACK_MODELS: List[str] = [
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nex-agi/nex-n2.5-mini:free",
    "liquid/lfm-2.5-2.6b:free",
]

def get_openrouter_headers() -> Dict[str, str]:
    api_key = get_openrouter_key()
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://arc-learns.onrender.com",
        "X-Title": "ARC LEARNS",
    }


def clean_reasoning_tokens(text: str) -> str:
    """Remove reasoning/thinking tokens (<think>...</think>) from output."""
    if not text:
        return ""
    # Remove <think> blocks
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove leading thinking process artifacts
    if "Here's a thinking process:" in cleaned:
        parts = cleaned.split("Here's a thinking process:")
        if len(parts) > 1 and "\n\n" in parts[1]:
            cleaned = parts[1].split("\n\n", 1)[-1]
    return cleaned.strip()


def call_llm_with_fallback(
    messages: List[Dict[str, str]],
    max_tokens: int = 1500,
    temperature: float = 0.7,
    timeout: float = 30.0,
) -> str:
    """Call OpenRouter with automatic failover across verified free models."""
    api_key = get_openrouter_key()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing. Returning fallback response.")
        return "Please configure your OPENROUTER_API_KEY in backend/.env to generate AI responses."

    headers = get_openrouter_headers()
    last_error = None

    for model in FALLBACK_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        for attempt in range(2):
            try:
                start_t = time.perf_counter()
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    elapsed = time.perf_counter() - start_t
                    logger.info("Generated via %s in %.2fs", model, elapsed)
                    return clean_reasoning_tokens(content)

                logger.warning(
                    "Model %s attempt %d returned %d: %s",
                    model,
                    attempt + 1,
                    resp.status_code,
                    resp.text[:100],
                )
                if resp.status_code == 429:
                    time.sleep(1.0)

            except Exception as e:
                last_error = e
                logger.warning("Model %s connection error: %s", model, e)
                time.sleep(0.5)

    raise RuntimeError(f"All AI models exhausted. Last error: {last_error}")


def call_llm_stream_with_fallback(
    messages: List[Dict[str, str]],
    max_tokens: int = 1500,
    temperature: float = 0.7,
    timeout: float = 30.0,
) -> Generator[str, None, None]:
    """Call OpenRouter with streaming, falling over to next model if initial connection fails."""
    api_key = get_openrouter_key()
    if not api_key:
        yield "Please configure your OPENROUTER_API_KEY in backend/.env."
        return

    headers = get_openrouter_headers()

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
                timeout=timeout,
            ) as response:
                if response.status_code != 200:
                    logger.warning("Stream failed on %s (%d), trying next model...", model, response.status_code)
                    continue

                in_think = False
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
                                    yield token
                        except Exception:
                            continue
                return
        except Exception as e:
            logger.warning("Stream error on %s: %s", model, e)

    # Fallback to non-streaming response if streaming connections break
    try:
        text = call_llm_with_fallback(messages, max_tokens=max_tokens, temperature=temperature)
        yield text
    except Exception as e:
        yield f"AI service temporarily busy. Please retry in a few seconds. ({e})"


# ============================================================
# HIGH LEVEL INTERFACES COMPATIBLE WITH EXISTING ROUTES
# ============================================================

def ask_openrouter(
    context: str,
    question: str,
    use_web_search: bool = False,
    response_format: Optional[Dict[str, Any]] = None,
) -> str:
    """ARC LEARNS AI Teacher non-streaming."""
    prompt = f"""You are ARC LEARNS, an expert educational AI Teacher.

INSTRUCTIONS:
- Use the study material provided below as your primary source.
- Explain concepts clearly, accurately, and step-by-step.
- Never invent facts not supported by the material.
- If the question cannot be answered from the material, politely explain that.

STUDY MATERIAL:
{context}

STUDENT QUESTION / TOPIC:
{question}
"""
    messages = [
        {"role": "system", "content": "You are ARC LEARNS, an encouraging and structured AI Teacher."},
        {"role": "user", "content": prompt},
    ]
    return call_llm_with_fallback(messages)


def ask_openrouter_stream(
    context: str,
    question: str,
    use_web_search: bool = False,
) -> Generator[str, None, None]:
    """ARC LEARNS AI Teacher streaming."""
    prompt = f"""You are ARC LEARNS, an expert educational AI Teacher.

INSTRUCTIONS:
- Teach the student using the study material provided below.
- Keep your explanation structured, clear, and engaging.
- Use headings, examples, and key points.

STUDY MATERIAL:
{context}

STUDENT QUESTION / TOPIC:
{question}
"""
    messages = [
        {"role": "system", "content": "You are ARC LEARNS, a helpful educational AI teacher."},
        {"role": "user", "content": prompt},
    ]
    return call_llm_stream_with_fallback(messages)


def ask_arc0(
    question: str,
    use_web_search: bool = True,
) -> str:
    """ARC 0 General Assistant non-streaming."""
    messages = [
        {"role": "system", "content": "You are ARC 0, an intelligent, versatile general-purpose AI assistant inside ARC LEARNS. Provide helpful, accurate, and structured answers on any topic."},
        {"role": "user", "content": question},
    ]
    return call_llm_with_fallback(messages)


def ask_arc0_stream(
    question: str,
    use_web_search: bool = True,
) -> Generator[str, None, None]:
    """ARC 0 General Assistant streaming."""
    messages = [
        {"role": "system", "content": "You are ARC 0, an intelligent, versatile general-purpose AI assistant inside ARC LEARNS. Provide helpful, accurate, and structured answers on any topic."},
        {"role": "user", "content": question},
    ]
    return call_llm_stream_with_fallback(messages)