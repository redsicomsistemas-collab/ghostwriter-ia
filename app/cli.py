from __future__ import annotations

import argparse
import csv

from app import db
from app.llm import embed_text
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag import retrieve_examples
from app.llm import generate_text


def init_db_command(_: argparse.Namespace) -> None:
    db.init_db()
    print("Base de datos lista.")


def ingest_csv_command(args: argparse.Namespace) -> None:
    db.init_db()
    count = 0
    with open(args.path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            text = (row.get("text") or "").strip()
            platform = (row.get("platform") or "unknown").strip()
            if not text:
                continue
            embedding = embed_text(text)
            db.insert_post(
                platform=platform,
                text=text,
                embedding=embedding,
                published_at=row.get("published_at") or None,
                url=row.get("url") or None,
            )
            count += 1
    print(f"Posts ingeridos: {count}")


def generate_command(args: argparse.Namespace) -> None:
    db.init_db()
    examples = retrieve_examples(args.topic, limit=args.examples, platform=args.platform)
    prompt = build_user_prompt(args.topic, args.platform, examples)
    content = generate_text(SYSTEM_PROMPT, prompt)
    draft_id = db.insert_draft(args.topic, args.platform, content, examples)
    print(f"Draft #{draft_id} ({args.platform})")
    print(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ghostwriter con IA")
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser("init-db")
    init_parser.set_defaults(func=init_db_command)

    ingest_parser = subparsers.add_parser("ingest-csv")
    ingest_parser.add_argument("path")
    ingest_parser.set_defaults(func=ingest_csv_command)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("topic")
    generate_parser.add_argument("--platform", default="linkedin")
    generate_parser.add_argument("--examples", type=int, default=3)
    generate_parser.set_defaults(func=generate_command)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
