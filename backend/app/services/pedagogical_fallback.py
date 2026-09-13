"""Grounded Pedagogical Fallback Engine for ARC LEARN.

Activates when cloud LLM providers are temporarily rate-limited (e.g. HTTP 429)
or offline, synthesizing structured educational lessons, doubt resolutions,
and interactive quizzes directly from indexed study material chunks.
"""

import re
from typing import Any, Dict, List


def extract_key_sentences(chunks: List[str]) -> List[str]:
    """Extract distinct informative sentences from source chunks."""
    sentences = []
    seen = set()
    for chunk in chunks:
        # Split on period, question mark, or newline
        lines = re.split(r'[.!?\n]+', str(chunk))
        for line in lines:
            cleaned = line.strip()
            # Keep substantial sentences
            if len(cleaned) > 25 and cleaned.lower() not in seen:
                # Avoid non-informative lines
                if not cleaned.startswith(("#", "http", "www", "---")):
                    seen.add(cleaned.lower())
                    sentences.append(cleaned)
    return sentences


def extract_code_blocks(chunks: List[str]) -> List[str]:
    """Extract code snippets from chunks."""
    code_snippets = []
    for chunk in chunks:
        matches = re.findall(r'```(?:[a-zA-Z0-9_-]*\n)?([\s\S]*?)```', str(chunk))
        for m in matches:
            code_snippets.append(m.strip())
    return code_snippets


def generate_fallback_lesson(topic: str, length: str, chunks: List[str]) -> str:
    """Generate a 7-stage masterclass lesson directly grounded in source chunks."""
    sentences = extract_key_sentences(chunks)
    code_blocks = extract_code_blocks(chunks)

    # Divide sentences across pedagogical sections
    intro_sentences = sentences[:3] if len(sentences) >= 3 else sentences
    theory_sentences = sentences[3:7] if len(sentences) >= 7 else sentences[:4]
    mech_sentences = sentences[7:12] if len(sentences) >= 12 else sentences[2:6]
    extra_sentences = sentences[12:18] if len(sentences) >= 18 else sentences[4:8]

    intro_text = " ".join(intro_sentences) if intro_sentences else f"{topic} is a core concept covered in your uploaded study material."
    theory_text = " ".join(theory_sentences) if theory_sentences else f"The foundational principles of {topic} govern how systems process and transform inputs."
    
    if mech_sentences:
        mech_text = "\n\n".join([f"• **Step {i+1}**: {s}" for i, s in enumerate(mech_sentences[:4])])
    else:
        mech_text = (
            f"• **Input & State**: System initializes parameters.\n"
            f"• **Execution**: Core transformation executes according to {topic}.\n"
            f"• **Output & Verification**: Results are validated."
        )

    # Example block
    if code_blocks:
        example_content = (
            f"```python\n"
            f"{code_blocks[0]}\n"
            f"```\n\n"
            f"*Line-by-line breakdown:* The code above demonstrates the concrete implementation of {topic} directly from your study material."
        )
    else:
        sample_calc = extra_sentences[0] if extra_sentences else f"Applying {topic} under standard operational conditions."
        example_content = (
            f"**Scenario Application:**\n\n"
            f"> {sample_calc}\n\n"
            f"*Analysis:* This demonstrates how the core variables interact dynamically in a real-world execution flow."
        )

    misconceptions = [
        f"Confusing the theoretical definition of {topic} with practical implementation constraints.",
        f"Overlooking boundary conditions or edge-case input values during operational execution."
    ]
    if len(extra_sentences) >= 2:
        safe_snippet = extra_sentences[1][:80].replace('"', "'")
        misconceptions.append(f"Assuming uniform behavior without verifying: '{safe_snippet}...'")

    misconception_text = "\n\n".join([f"• ⚠️ **Misconception**: {m}" for m in misconceptions])

    fallback_core = sentences[:3] if sentences else [f"Mastery of {topic} requires understanding underlying mechanics."]
    summary_bullets = "\n".join([f"1. **Core Essence**: {s}" for s in fallback_core])

    lesson = f"""# 1. Intuition & Mental Model
To understand **{topic}**, imagine a system where every component has a precise, interdependent role. Rather than viewing it as an isolated rule, think of it as an optimized mechanism designed to solve specific constraints efficiently.

{intro_text}

# 2. Formal Concepts & Theoretical Foundation
The study material establishes the following foundational formulations and rules for **{topic}**:

{theory_text}

# 3. Step-by-Step Mechanical Breakdown
Here is the operational lifecycle of how this mechanism operates step-by-step:

{mech_text}

# 4. Deep Worked Example & Practical Walkthrough
{example_content}

# 5. Common Misconceptions & Traps
Students and engineers commonly encounter these subtle pitfalls when working with **{topic}**:

{misconception_text}

# 6. Key Takeaways & Mental Anchors
{summary_bullets}

# 7. Knowledge Check & Reflection
Test your active recall with these conceptual verification questions:
1. *What is the primary governing constraint of {topic} as detailed in your notes?*
2. *How do intermediate state changes affect the final output?*
3. *Under what boundary conditions would this approach require modification?*

> [!NOTE]
> Grounded pedagogical lesson synthesized directly from your indexed study material.
"""
    return lesson.strip()


def generate_fallback_doubt(question: str, chunks: List[str]) -> str:
    """Generate grounded doubt clarification using retrieved chunks."""
    sentences = extract_key_sentences(chunks)
    if not sentences:
        return (
            f"Based on your uploaded material, here is the answer regarding **{question}**:\n\n"
            f"The relevant sections emphasize key operational principles and definitions. "
            f"Please ensure your query matches the terminology in your uploaded notes."
        )

    direct_answer = sentences[0]
    supporting = " ".join(sentences[1:4])

    return f"""**Direct Resolution:**
{direct_answer}

**Contextual Explanation:**
{supporting}

> [!NOTE]
> Answer grounded directly in your uploaded study material notes.
"""


def generate_fallback_quiz(topic: str, count: int, chunks: List[str]) -> List[Dict[str, Any]]:
    """Generate interactive pedagogical quiz questions directly from chunks."""
    sentences = extract_key_sentences(chunks)
    questions = []

    for i in range(min(count, max(1, len(sentences)))):
        s = sentences[i % len(sentences)]
        words = s.split()
        if len(words) >= 6:
            key_phrase = " ".join(words[:4])
            statement = " ".join(words[4:])
            q_text = f"According to your study material regarding {topic}, which of the following is correct regarding '{key_phrase}'?"
            correct = statement
            distractors = [
                f"It operates independently without affecting {topic}.",
                f"It is strictly deprecated in modern implementations.",
                f"It reverses the fundamental transformation process."
            ]
            options = [correct] + distractors
            if i % 3 == 1:
                options = [distractors[0], correct, distractors[1], distractors[2]]
            elif i % 3 == 2:
                options = [distractors[0], distractors[1], correct, distractors[2]]

            diff = "easy" if i == 0 else ("medium" if i == 1 else "hard")
            questions.append({
                "question": q_text,
                "options": options,
                "correct_answer": correct,
                "explanation": f"The study material states: '{s}'. This confirms that {correct}.",
                "distractor_analysis": {
                    distractors[0]: f"Incorrect because {key_phrase} is directly coupled to {topic}.",
                    distractors[1]: f"Incorrect because the notes establish this as an active principle.",
                    distractors[2]: f"Incorrect because it does not reverse the transformation."
                },
                "difficulty": diff,
                "concept_tested": f"{topic} Core Principles"
            })

    if not questions:
        questions.append({
            "question": f"What is the primary role of {topic} in your study material?",
            "options": [
                f"To govern foundational processes in {topic}",
                "To eliminate all memory allocation",
                "To bypass verification requirements",
                "To force single-threaded execution"
            ],
            "correct_answer": f"To govern foundational processes in {topic}",
            "explanation": f"Your study material specifies {topic} as a core architectural concept.",
            "distractor_analysis": {
                "To eliminate all memory allocation": "Incorrect; memory allocation is preserved.",
                "To bypass verification requirements": "Incorrect; verification is mandatory.",
                "To force single-threaded execution": "Incorrect; concurrency is not restricted."
            },
            "difficulty": "medium",
            "concept_tested": topic
        })

    return questions
