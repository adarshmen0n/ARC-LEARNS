"""Unit and integration tests for ARC Zero 2026 Real-Time Grounding & Speed."""

import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.web_search import (
    get_temporal_grounding,
    search_live_web,
    build_grounded_arc0_prompt
)
from app.services.ai_manager import ask_arc0


def test_temporal_grounding_tamil_nadu():
    grounding = get_temporal_grounding("Who is the Chief Minister of Tamil Nadu?")
    assert grounding is not None
    assert "Vijay" in grounding
    assert "2026" in grounding


def test_temporal_grounding_chatgpt6():
    grounding = get_temporal_grounding("When did ChatGPT-6 Astra release?")
    assert grounding is not None
    assert "ChatGPT-6 Astra" in grounding
    assert "2026" in grounding


def test_build_grounded_arc0_prompt():
    prompt = build_grounded_arc0_prompt("Who is the Chief Minister of Tamil Nadu?")
    assert "ARC ZERO" in prompt
    assert "2026" in prompt
    assert "Vijay" in prompt


def test_arc0_live_answers_tamil_nadu():
    answer = ask_arc0("Who is the Chief Minister of Tamil Nadu?")
    assert "Vijay" in answer


def test_arc0_live_answers_chatgpt6():
    answer = ask_arc0("When did the ChatGPT-6 Astra release?")
    assert "2026" in answer
