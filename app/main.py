from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.llm import embed_text, generate_text
from app.prompts import IDEAS_SYSTEM_PROMPT, SYSTEM_PROMPT, build_ideas_prompt, build_user_prompt
from app.publishers.buffer import publish_to_buffer
from app.rag import retrieve_examples, style_profile
from app.schemas import DraftOut, GenerateRequest, IdeasRequest, PostIngest


app = FastAPI(title="Ghostwriter con IA", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.post("/posts/ingest")
def ingest_post(payload: PostIngest) -> dict:
    embedding = embed_text(payload.text)
    post_id = db.insert_post(
        platform=payload.platform,
        text=payload.text,
        embedding=embedding,
        published_at=payload.published_at,
        url=payload.url,
    )
    return {"id": post_id}


@app.get("/style-profile")
def get_style_profile(topic: str, platform: str | None = None) -> dict:
    examples = retrieve_examples(topic=topic, platform=platform)
    return {"profile": style_profile(examples), "examples": examples}


@app.post("/ideas")
def ideas(payload: IdeasRequest) -> dict:
    examples = retrieve_examples(topic=payload.topic, limit=payload.examples)
    prompt = build_ideas_prompt(payload.topic, examples, payload.brand_context)
    content = generate_text(IDEAS_SYSTEM_PROMPT, prompt)
    return {"ideas": content, "examples": examples}


@app.post("/generate")
def generate(payload: GenerateRequest) -> dict:
    drafts = []
    for platform in payload.platforms:
        examples = retrieve_examples(
            topic=payload.topic,
            limit=payload.examples_per_platform,
            platform=platform,
        )
        user_prompt = build_user_prompt(
            topic=payload.topic,
            platform=platform,
            examples=examples,
            brand_context=payload.brand_context,
        )
        content = generate_text(SYSTEM_PROMPT, user_prompt)
        draft_id = db.insert_draft(payload.topic, platform, content, examples)
        drafts.append({"id": draft_id, "platform": platform, "content": content, "examples": examples})
    return {"drafts": drafts}


@app.get("/drafts", response_model=list[DraftOut])
def drafts(status: str | None = None) -> list[dict]:
    return [dict(row) for row in db.list_drafts(status=status)]


@app.post("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int) -> dict:
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft no encontrado")
    db.update_draft_status(draft_id, "approved")
    return {"id": draft_id, "status": "approved"}


@app.post("/drafts/{draft_id}/publish/buffer")
def publish_buffer(draft_id: int) -> dict:
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft no encontrado")
    if draft["status"] != "approved":
        raise HTTPException(status_code=409, detail="Aprueba el draft antes de publicarlo")

    result = publish_to_buffer(platform=draft["platform"], text=draft["content"])
    db.update_draft_status(draft_id, "published")
    return {"id": draft_id, "status": "published", "buffer": result}


@app.get("/drafts/{draft_id}/examples")
def draft_examples(draft_id: int) -> dict:
    draft = db.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft no encontrado")
    return {"examples": json.loads(draft["examples"])}
