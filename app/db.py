from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Iterator

from app.config import settings


def _sqlite_path() -> Path:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        raise ValueError("Este MVP usa SQLite. Configura DATABASE_URL=sqlite:///./ghostwriter.db")
    return Path(settings.database_url.removeprefix(prefix))


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    db_path = _sqlite_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                text TEXT NOT NULL,
                published_at TEXT,
                url TEXT,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                platform TEXT NOT NULL,
                content TEXT NOT NULL,
                examples TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL
            );
            """
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def insert_post(platform: str, text: str, embedding: list[float], published_at: str | None = None, url: str | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (platform, text, published_at, url, embedding, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (platform, text, published_at, url, json.dumps(embedding), now_iso()),
        )
        return int(cur.lastrowid)


def list_posts() -> list[sqlite3.Row]:
    with connect() as conn:
        return list(conn.execute("SELECT * FROM posts ORDER BY id DESC"))


def insert_draft(topic: str, platform: str, content: str, examples: list[dict]) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO drafts (topic, platform, content, examples, status, created_at)
            VALUES (?, ?, ?, ?, 'draft', ?)
            """,
            (topic, platform, content, json.dumps(examples, ensure_ascii=True), now_iso()),
        )
        return int(cur.lastrowid)


def list_drafts(status: str | None = None) -> list[sqlite3.Row]:
    with connect() as conn:
        if status:
            return list(conn.execute("SELECT * FROM drafts WHERE status = ? ORDER BY id DESC", (status,)))
        return list(conn.execute("SELECT * FROM drafts ORDER BY id DESC"))


def get_draft(draft_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()


def update_draft_status(draft_id: int, status: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE drafts SET status = ? WHERE id = ?", (status, draft_id))
