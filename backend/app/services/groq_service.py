"""GroqCloud API service for ARC LEARN.

Tier 2 Secondary Provider: World's fastest inference engine (300-500+ tokens/second),
providing instantaneous ChatGPT-grade responses via custom LPUs.
Implemented via OpenAI-compatible REST API using HTTPX.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Generator, List, Optional
from dotenv import load_dotenv
import httpx

load_dotenv()

logger = logging.getLogger("arc_learns.groq_service")


def clean_reasoning_tokens(text: str) -> str:
    """Strip internal thinking/reasoning tags from model outputs."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<think>.*", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()

# Candidate Groq models in order of priority (qwen3.8-27b delivers < 0.8s latency)
GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-120b",
]

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def get_groq_key() -> Optional[str]:
    """Retrieve Groq API key from environment."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    return key if key else None


def call_groq(
    messages: List[Dict[str, str]],
    max_tokens: int = 2500,
    temperature: float = 0.7,
    timeout: float = 20.0,
) -> str:
    """Synchronous call to Groq API with model fallback."""
    api_key = get_groq_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    client_timeout = httpx.Timeout(connect=4.0, read=timeout, write=5.0, pool=5.0)

    last_error: Optional[Exception] = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            start_t = time.perf_counter()
            with httpx.Client(timeout=client_timeout) as client:
                resp = client.post(GROQ_ENDPOINT, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                raw_content = data["choices"][0]["message"].get("content") or ""
                content = clean_reasoning_tokens(raw_content)
                elapsed = time.perf_counter() - start_t
                logger.info("Generated via Groq (%s) in %.2fs", model, elapsed)
                if content:
                    return content.strip()

            logger.warning("Groq %s returned %d: %s", model, resp.status_code, resp.text[:120])
        except Exception as e:
            last_error = e
            logger.warning("Groq %s error: %s", model, e)

    raise RuntimeError(f"All Groq models exhausted. Last error: {last_error}")


def call_groq_stream(
    messages: List[Dict[str, str]],
    max_tokens: int = 2500,
    temperature: float = 0.7,
    timeout: float = 25.0,
) -> Generator[str, None, None]:
    """Stream ultra-fast tokens from Groq API via SSE."""
    api_key = get_groq_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    stream_timeout = httpx.Timeout(connect=3.0, read=timeout, write=5.0, pool=5.0)

    last_error: Optional[Exception] = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        try:
            with httpx.stream("POST", GROQ_ENDPOINT, headers=headers, json=payload, timeout=stream_timeout) as response:
                if response.status_code != 200:
                    logger.warning("Groq stream %s returned %d", model, response.status_code)
                    continue

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
                                tokens_yielded += 1
                                yield token
                        except Exception:
                            continue

                if tokens_yielded > 0:
                    return
        except Exception as e:
            last_error = e
            logger.warning("Groq stream error on %s: %s", model, e)

    # Fallback to non-streaming if stream drops
    text = call_groq(messages, max_tokens=max_tokens, temperature=temperature)
    yield text
