from __future__ import annotations

from app.config import settings


PLATFORM_RULES = {
    "linkedin": "Profesional, claro, con una idea fuerte al inicio y cierre conversacional. Evita hashtags excesivos.",
    "x": "Directo, breve, con frases compactas. Si conviene, usa formato de hilo numerado.",
    "instagram": "Visual, humano, con caption escaneable y llamada a comentar.",
}


SYSTEM_PROMPT = """Actua como un ghostwriter senior de redes sociales.
Tu tarea es escribir como el usuario, no como una marca generica.
No inventes datos. No uses adjetivos vagos como "increible" o "fascinante" salvo que aparezcan en los ejemplos.
Respeta el nivel de formalidad, longitud de oraciones, tecnicismos, ritmo y uso de emojis observado.
Devuelve solo el post final, sin explicaciones."""


IDEAS_SYSTEM_PROMPT = """Actua como estratega editorial para redes sociales.
Genera angulos concretos, utiles y publicables. Evita ideas genericas.
Devuelve solo una lista numerada de 3 angulos, cada uno con una tesis clara."""


def build_user_prompt(topic: str, platform: str, examples: list[dict], brand_context: str | None = None) -> str:
    examples_text = "\n\n".join(
        f"Ejemplo {index + 1} ({example['platform']}, score {example['score']:.3f}):\n{example['text']}"
        for index, example in enumerate(examples)
    )
    platform_rule = PLATFORM_RULES.get(platform.lower(), "Adapta el contenido al formato natural de la plataforma.")

    return f"""
Contexto de marca:
{brand_context or settings.default_brand_context}

Tema o noticia:
{topic}

Plataforma destino:
{platform}

Reglas de plataforma:
{platform_rule}

Ejemplos recuperados por similitud:
{examples_text or "No hay ejemplos disponibles todavia."}

Instrucciones:
1. Identifica los patrones de tono de los ejemplos.
2. Escribe un post original sobre el tema.
3. Mantén el estilo del usuario sin copiar literalmente.
4. No agregues encabezados, notas ni analisis.
""".strip()


def build_ideas_prompt(topic: str, examples: list[dict], brand_context: str | None = None) -> str:
    examples_text = "\n\n".join(
        f"Ejemplo {index + 1} ({example['platform']}):\n{example['text']}"
        for index, example in enumerate(examples)
    )
    return f"""
Contexto de marca:
{brand_context or settings.default_brand_context}

Noticia, tendencia o tema:
{topic}

Ejemplos de estilo del usuario:
{examples_text or "No hay ejemplos disponibles todavia."}

Genera 3 angulos distintos para convertir este tema en contenido de redes.
Cada angulo debe incluir una postura, no solo un titulo.
""".strip()
