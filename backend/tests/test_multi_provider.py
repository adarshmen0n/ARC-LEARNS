"""Unit and integration tests for ARC LEARN Multi-Provider Architecture.

Tests:
- Google Gemini payload translation and error handling
- Groq payload execution and fallback
- ai_manager 4-tier waterfall resolution
- Status reporting and resilience
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ai_manager import (
    ask_ai,
    ask_arc0,
    build_unified_messages,
    get_provider_status,
)
from app.services.gemini_service import format_gemini_payload


def test_gemini_payload_formatting():
    messages = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": "Explain gradient descent."},
        {"role": "assistant", "content": "Gradient descent minimizes error."},
        {"role": "user", "content": "What is learning rate?"},
    ]

    payload = format_gemini_payload(messages, max_tokens=1000, temperature=0.5)

    assert "contents" in payload
    assert "system_instruction" in payload
    assert payload["system_instruction"]["parts"][0]["text"] == "You are a teacher."

    contents = payload["contents"]
    assert len(contents) == 3
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "Explain gradient descent."
    assert contents[1]["role"] == "model"
    assert contents[1]["parts"][0]["text"] == "Gradient descent minimizes error."
    assert contents[2]["role"] == "user"
    assert contents[2]["parts"][0]["text"] == "What is learning rate?"
    assert payload["generationConfig"]["maxOutputTokens"] == 1000


def test_build_unified_messages():
    context = "Chapter 1: Intro to Neural Networks."
    question = "What is an activation function?"
    history = [
        {"role": "user", "content": "Hello."},
        {"role": "assistant", "content": "Hi there!"},
    ]

    messages = build_unified_messages(context, question, history=history)

    assert messages[0]["role"] == "system"
    assert "ARC LEARN" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Hello."
    assert messages[2]["role"] == "assistant"
    assert messages[2]["content"] == "Hi there!"
    assert "STUDY MATERIAL:" in messages[3]["content"]
    assert "activation function" in messages[3]["content"]


def test_provider_status_reporting():
    status = get_provider_status()
    assert "gemini" in status
    assert "groq" in status
    assert "openrouter" in status
    assert status["grounded_fallback"] is True
    assert status["active_primary"] in ("gemini", "groq", "openrouter", "grounded_fallback")


def test_cascade_gemini_to_groq():
    with patch("app.services.ai_manager.get_gemini_key", return_value="mock-gemini-key"), \
         patch("app.services.ai_manager.get_groq_key", return_value="mock-groq-key"), \
         patch("app.services.ai_manager.call_gemini", side_effect=RuntimeError("Gemini 429 Quota Exceeded")), \
         patch("app.services.ai_manager.call_groq", return_value="Response from Groq LPU"):

        result = ask_ai("", "What is deep learning?")
        assert result == "Response from Groq LPU"


def test_cascade_groq_to_openrouter():
    with patch("app.services.ai_manager.get_gemini_key", return_value=None), \
         patch("app.services.ai_manager.get_groq_key", return_value="mock-groq-key"), \
         patch("app.services.ai_manager.get_openrouter_key", return_value="mock-or-key"), \
         patch("app.services.ai_manager.call_groq", side_effect=RuntimeError("Groq 429 Rate Limited")), \
         patch("app.services.ai_manager.ask_openrouter", return_value="Response from OpenRouter Gemma"):

        result = ask_ai("", "What is deep learning?")
        assert result == "Response from OpenRouter Gemma"


def test_cascade_all_exhausted_raises_runtime_error():
    with patch("app.services.ai_manager.get_gemini_key", return_value=None), \
         patch("app.services.ai_manager.get_groq_key", return_value=None), \
         patch("app.services.ai_manager.get_openrouter_key", return_value="mock-or-key"), \
         patch("app.services.ai_manager.ask_openrouter", side_effect=RuntimeError("OpenRouter 429")):

        with pytest.raises(RuntimeError) as exc_info:
            ask_ai("", "What is deep learning?")
        assert "All cloud AI providers exhausted" in str(exc_info.value)


def test_arc0_graceful_status_when_exhausted():
    with patch("app.services.ai_manager.get_gemini_key", return_value=None), \
         patch("app.services.ai_manager.get_groq_key", return_value=None), \
         patch("app.services.ai_manager.get_openrouter_key", return_value=None):

        result = ask_arc0("Hello world")
        assert "ARC Zero Status Notice" in result
