from functools import lru_cache

from groq import Groq

from app.config import get_settings


@lru_cache
def get_client() -> Groq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your key from https://console.groq.com/keys"
        )
    return Groq(api_key=settings.groq_api_key)


def chat_completion(
    messages: list[dict], temperature: float = 0.2, response_format_json: bool = False
) -> str:
    settings = get_settings()
    client = get_client()
    kwargs = {}
    if response_format_json:
        kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return completion.choices[0].message.content
