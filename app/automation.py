from __future__ import annotations

import random
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
import feedparser

from app import db
from app.config import settings
from app.llm import generate_text
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.publishers.buffer import publish_to_buffer
from app.rag import retrieve_examples


scheduler: BackgroundScheduler | None = None


def _topic_from_feed_entry(entry: Any) -> str:
    title = getattr(entry, "title", "") or entry.get("title", "")
    summary = getattr(entry, "summary", "") or entry.get("summary", "")
    link = getattr(entry, "link", "") or entry.get("link", "")
    return f"{title}\n{summary}\nFuente: {link}".strip()


def collect_topics() -> list[tuple[str, str]]:
    configured_topics = [("manual", topic) for topic in settings.auto_content_topics]
    feed_topics: list[tuple[str, str]] = []

    if settings.auto_content_feed_url:
        feed = feedparser.parse(settings.auto_content_feed_url)
        for entry in feed.entries[: max(settings.auto_post_limit_per_run * 3, 3)]:
            topic = _topic_from_feed_entry(entry)
            if topic:
                feed_topics.append(("rss", topic))

    topics = configured_topics + feed_topics
    random.shuffle(topics)
    return topics[: settings.auto_post_limit_per_run]


def generate_and_optionally_publish(source: str, topic: str) -> list[dict]:
    created: list[dict] = []
    platforms = settings.auto_content_platforms or ["linkedin"]

    for platform in platforms:
        examples = retrieve_examples(topic=topic, limit=3, platform=platform)
        prompt = build_user_prompt(
            topic=topic,
            platform=platform,
            examples=examples,
            brand_context=settings.default_brand_context,
        )
        content = generate_text(SYSTEM_PROMPT, prompt)
        draft_id = db.insert_draft(topic, platform, content, examples)
        status = "draft"
        publish_result: dict | None = None

        if settings.auto_publish_enabled:
            publish_result = publish_to_buffer(platform=platform, text=content)
            db.update_draft_status(draft_id, "published")
            status = "published"

        created.append(
            {
                "id": draft_id,
                "platform": platform,
                "status": status,
                "publish_result": publish_result,
            }
        )

    db.insert_automation_run(source=source, topic=topic, status="ok", message=f"Creados: {len(created)}")
    return created


def run_automation_once() -> dict:
    db.init_db()
    topics = collect_topics()
    if not topics:
        db.insert_automation_run(
            source="automation",
            topic="",
            status="skipped",
            message="No hay AUTO_CONTENT_TOPICS ni AUTO_CONTENT_FEED_URL configurados.",
        )
        return {"created": [], "message": "No hay temas configurados."}

    created = []
    for source, topic in topics:
        try:
            created.extend(generate_and_optionally_publish(source, topic))
        except Exception as exc:
            db.insert_automation_run(source=source, topic=topic, status="error", message=str(exc))
            raise
    return {"created": created}


def start_scheduler() -> None:
    global scheduler
    if not settings.auto_mode_enabled:
        return
    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_automation_once,
        "interval",
        minutes=max(settings.auto_post_interval_minutes, 15),
        id="auto_content_job",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()


def stop_scheduler() -> None:
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
