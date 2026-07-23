import json

from app.llm.groq_client import chat_completion
from app.schemas import QuizQuestion

SYSTEM_PROMPT = (
    "You are StudyMate, an AI study assistant that writes revision quizzes. "
    "Given study material, generate multiple-choice questions that test "
    "understanding of the material. Always respond with a JSON object only."
)

# Keep the prompt within a safe context budget for the hosted model.
_MAX_CONTEXT_CHARS = 8000


def _build_prompt(text: str, num_questions: int) -> str:
    return (
        f"Study material:\n{text}\n\n"
        f"Write exactly {num_questions} multiple-choice questions covering the "
        "key concepts in this material. Respond with a JSON object of the exact "
        "shape:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "string",\n'
        '      "options": ["string", "string", "string", "string"],\n'
        '      "correct_index": 0,\n'
        '      "explanation": "string"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Each question must have exactly 4 options and correct_index must be the "
        "0-based index of the correct option."
    )


def generate_quiz(chunks: list[str], num_questions: int = 5) -> list[QuizQuestion]:
    if not chunks:
        return []

    combined = ""
    for chunk in chunks:
        if len(combined) + len(chunk) > _MAX_CONTEXT_CHARS:
            break
        combined = f"{combined}\n\n{chunk}"

    raw = chat_completion(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(combined.strip(), num_questions)},
        ],
        temperature=0.4,
        response_format_json=True,
    )

    data = json.loads(raw)
    questions = data.get("questions", [])
    return [QuizQuestion(**q) for q in questions]
