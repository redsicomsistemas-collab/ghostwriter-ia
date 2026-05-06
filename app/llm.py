from __future__ import annotations

from openai import OpenAI

from app.config import settings


def client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en el entorno o .env")
    return OpenAI(api_key=settings.openai_api_key)


def embed_text(text: str) -> list[float]:
    result = client().embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return result.data[0].embedding


def generate_text(system_prompt: str, user_prompt: str) -> str:
    result = client().responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return result.output_text.strip()
