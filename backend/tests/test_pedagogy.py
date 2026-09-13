import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.api.teach import build_teach_prompt, validate_length, prepare_context
from app.api.chat import build_doubt_prompt
from app.api.quiz import clean_json_response, validate_quiz, build_quiz_prompt
from app.services.vector_store import create_vector_store
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_teach_prompt_structure():
    context = "Backpropagation computes the gradient of the loss function with respect to weights."
    for length in ["short", "medium", "long"]:
        prompt = build_teach_prompt("Backpropagation", length, context)
        assert "ARC LEARN" in prompt
        assert "# 1. Intuition & Mental Model" in prompt
        assert "# 2. Formal Concepts & Theoretical Foundation" in prompt
        assert "# 3. Step-by-Step Mechanical Breakdown" in prompt
        assert "# 4. Deep Worked Example & Practical Walkthrough" in prompt
        assert "# 5. Common Misconceptions & Traps" in prompt
        assert "# 6. Key Takeaways & Mental Anchors" in prompt
        assert "# 7. Knowledge Check & Reflection" in prompt
        assert length.upper() in prompt

def test_teach_length_validation():
    assert validate_length("short") == "short"
    assert validate_length("LONG") == "long"
    assert validate_length("invalid_length") == "medium"

def test_chat_doubt_prompt():
    prompt = build_doubt_prompt("What is gradient vanishing?", "Vanishing gradient happens in deep networks.")
    assert "ARC LEARN AI Tutor" in prompt
    assert "What is gradient vanishing?" in prompt
    assert "Vanishing gradient" in prompt

def test_quiz_json_cleaning_and_validation():
    raw_ai_response = """
    ```json
    {
        "topic": "Neural Networks",
        "quiz": [
            {
                "question": "What is the primary purpose of activation functions in neural networks?",
                "options": [
                    "To introduce non-linearity",
                    "To decrease computational cost",
                    "To prevent weight updates",
                    "To sort training data"
                ],
                "correct_answer": "To introduce non-linearity",
                "explanation": "Activation functions allow neural networks to learn complex non-linear mappings.",
                "distractor_analysis": {
                    "To decrease computational cost": "Activation functions actually add computational overhead.",
                    "To prevent weight updates": "Weights must update during gradient descent.",
                    "To sort training data": "Data sorting is not handled by activation functions."
                },
                "difficulty": "medium",
                "concept_tested": "Activation Functions"
            }
        ]
    }
    ```
    """
    cleaned = clean_json_response(raw_ai_response)
    assert cleaned.startswith("{")
    assert cleaned.endswith("}")

    import json
    data = json.loads(cleaned)
    valid_quiz = validate_quiz(data["quiz"], expected_count=1)
    assert len(valid_quiz) == 1
    q = valid_quiz[0]
    assert q["question"] == "What is the primary purpose of activation functions in neural networks?"
    assert len(q["options"]) == 4
    assert q["correct_answer"] == "To introduce non-linearity"
    assert "non-linear mappings" in q["explanation"]
    assert "Activation Functions" in q["concept_tested"]
    assert q["difficulty"] == "medium"
    assert len(q["distractor_analysis"]) == 3

def test_quiz_cleaning_array_wrap():
    raw_array = """[{"question": "Q1?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "Exp"}]"""
    cleaned = clean_json_response(raw_array)
    import json
    parsed = json.loads(cleaned)
    assert "quiz" in parsed
    assert len(parsed["quiz"]) == 1

def test_api_routes_smoke():
    resp = client.post("/arc0", json={"question": ""})
    assert resp.status_code == 200
    assert "Please enter a question" in resp.json()["answer"]

    resp = client.post("/chat", json={"question": ""})
    assert resp.status_code == 200
    assert "Please enter a question" in resp.json()["answer"]
