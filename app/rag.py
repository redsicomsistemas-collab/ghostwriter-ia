from __future__ import annotations

import json
import math

from app import db
from app.llm import embed_text


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def retrieve_examples(topic: str, limit: int = 3, platform: str | None = None) -> list[dict]:
    query_embedding = embed_text(topic)
    scored: list[dict] = []

    for row in db.list_posts():
        if platform and row["platform"].lower() != platform.lower():
            continue
        embedding = json.loads(row["embedding"])
        scored.append(
            {
                "id": row["id"],
                "platform": row["platform"],
                "text": row["text"],
                "published_at": row["published_at"],
                "url": row["url"],
                "score": cosine_similarity(query_embedding, embedding),
            }
        )

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def style_profile(examples: list[dict]) -> str:
    if not examples:
        return "No hay ejemplos previos. Mantén un tono claro, directo y humano."

    texts = [item["text"] for item in examples]
    avg_words = round(sum(len(text.split()) for text in texts) / len(texts))
    emoji_count = sum(1 for text in texts for char in text if ord(char) > 10000)
    question_count = sum(text.count("?") for text in texts)

    return (
        f"Promedio aproximado: {avg_words} palabras. "
        f"Uso de emojis observado: {emoji_count}. "
        f"Preguntas retoricas observadas: {question_count}. "
        "Replica patrones visibles de ritmo, vocabulario y estructura sin copiar frases."
    )
