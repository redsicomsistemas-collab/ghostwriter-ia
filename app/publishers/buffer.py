from __future__ import annotations

import httpx

from app.config import settings


BUFFER_API_URL = "https://api.bufferapp.com/1/updates/create.json"


def publish_to_buffer(platform: str, text: str) -> dict:
    if not settings.buffer_access_token:
        raise RuntimeError("Falta BUFFER_ACCESS_TOKEN para publicar con Buffer")
    profile_id = settings.buffer_profile_ids.get(platform.lower())
    if not profile_id:
        raise RuntimeError(f"Falta profile id de Buffer para la plataforma: {platform}")

    response = httpx.post(
        BUFFER_API_URL,
        data={
            "access_token": settings.buffer_access_token,
            "text": text,
            "now": "false",
            "profile_ids[]": profile_id,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
