from __future__ import annotations

import argparse

import feedparser

from app import db
from app.llm import generate_text
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag import retrieve_examples


def topic_from_entry(entry: dict) -> str:
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    link = entry.get("link", "")
    return f"{title}\n{summary}\nFuente: {link}".strip()


def run(feed_url: str, platform: str, limit: int) -> None:
    db.init_db()
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:limit]:
        topic = topic_from_entry(entry)
        examples = retrieve_examples(topic, platform=platform)
        prompt = build_user_prompt(topic, platform, examples)
        content = generate_text(SYSTEM_PROMPT, prompt)
        draft_id = db.insert_draft(topic, platform, content, examples)
        print(f"Draft creado: {draft_id} ({platform})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera drafts desde un RSS")
    parser.add_argument("feed_url")
    parser.add_argument("--platform", default="linkedin")
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()
    run(args.feed_url, args.platform, args.limit)


if __name__ == "__main__":
    main()
