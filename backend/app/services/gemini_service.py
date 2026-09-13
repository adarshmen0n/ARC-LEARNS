"""Google Gemini API service for ARC LEARN.

Tier 1 Primary Provider: Offers generous free tier (1,500 requests/day),
1M token context window, and sub-second generation speeds.
Implemented via direct HTTPX REST integration without heavy dependencies.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()

logger = logging.getLogger("arc_learns.gemini_service")

# Candidate models in order of priority
GEMINI_MODELS = [
    "gemini-3-flash-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
]

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_gemini_key() -> Optional[str]:
    """Retrieve Gemini API key from environment."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return key if key else None


def format_gemini_payload(
    messages: List[Dict[str, str]],
    max_tokens: int = 2500,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Translate standard chat messages (system, user, assistant) into Gemini payload."""
    contents: List[Dict[str, Any]] = []
    system_texts: List[str] = []

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if not content:
            continue

        if role == "system":
            system_texts.append(content)
        elif role in ("assistant", "model"):
            contents.append({
                "role": "model",
                "parts": [{"text": content}]
            })
        else:  # user
            contents.append({
                "role": "user",
                "parts": [{"text": content}]
            })

    # Gemini requires at least one content part
    if not contents:
        contents.append({
            "role": "user",
            "parts": [{"text": "Hello"}]
        })

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    if system_texts:
        payload["system_instruction"] = {
            "parts": [{"text": "\n\n".join(system_texts)}]
        }

    return payload


def call_gemini(
    messages: List[Dict[str, str]],
    max_tokens: int = 2500,
    temperature: float = 0.7,
    timeout: float = 25.0,
) -> str:
    """Synchronous call to Gemini API with model fallback."""
    api_key = get_gemini_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    payload = format_gemini_payload(messages, max_tokens, temperature)
    client_timeout = httpx.Timeout(connect=5.0, read=timeout, write=5.0, pool=5.0)

    last_error: Optional[Exception] = None
    for model in GEMINI_MODELS:
        url = f"{BASE_URL}/{model}:generateContent?key={api_key}"
        try:
            start_t = time.perf_counter()
            with httpx.Client(timeout=client_timeout) as client:
                resp = client.post(url, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts)
                    if text.strip():
                        elapsed = time.perf_counter() - start_t
                        logger.info("Generated via Gemini (%s) in %.2fs", model, elapsed)
                        return text.strip()

            logger.warning("Gemini %s returned %d: %s", model, resp.status_code, resp.text[:120])
        except Exception as e:
            last_error = e
            logger.warning("Gemini %s error: %s", model, e)

    raise RuntimeError(f"All Gemini models exhausted. Last error: {last_error}")


def call_gemini_stream(
    messages: List[Dict[str, str]],
    max_tokens: int = 2500,
    temperature: float = 0.7,
    timeout: float = 30.0,
) -> Generator[str, None, None]:
    """Stream response tokens from Gemini API via Server-Sent Events (SSE)."""
    api_key = get_gemini_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    payload = format_gemini_payload(messages, max_tokens, temperature)
    stream_timeout = httpx.Timeout(connect=4.0, read=timeout, write=5.0, pool=5.0)

    last_error: Optional[Exception] = None
    for model in GEMINI_MODELS:
        url = f"{BASE_URL}/{model}:streamGenerateContent?key={api_key}&alt=sse"
        try:
            with httpx.stream("POST", url, json=payload, timeout=stream_timeout) as response:
                if response.status_code != 200:
                    logger.warning("Gemini stream %s returned %d", model, response.status_code)
                    continue

                tokens_yielded = 0
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if not data_str or data_str == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(data_str)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    t = p.get("text", "")
                                    if t:
                                        tokens_yielded += 1
                                        yield t
                        except Exception:
                            continue

                if tokens_yielded > 0:
                    return
        except Exception as e:
            last_error = e
            logger.warning("Gemini stream error on %s: %s", model, e)

    # Fallback to non-streaming if stream interrupted
    text = call_gemini(messages, max_tokens=max_tokens, temperature=temperature)
    yield text