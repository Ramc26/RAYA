#!/usr/bin/env python3
"""
Extract ChatGPT export into unified JSONL (same shape as gemini_raw.jsonl).

Place OpenAI's export zip or conversations.json under data/raw/chatgpt/, then:

    python3 scripts/parse_chatgpt.py

Default input search order:
    data/raw/chatgpt/conversations.json
    data/raw/chatgpt/export.zip
    data/raw/chatgpt/*.zip

Output:
    data/processed/chatgpt_raw.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path


DEFAULT_OUTPUT = Path("data/processed/chatgpt_raw.jsonl")
DEFAULT_RAW_DIR = Path("data/raw/chatgpt")


def clean_text(text: str) -> str:
    text = text or ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def format_timestamp(value: float | int | None) -> str | None:
    if value is None:
        return None
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return None
    # Match Gemini-style strings used elsewhere in the pipeline.
    return datetime.fromtimestamp(ts).strftime("%b %d, %Y, %I:%M:%S %p IST")


def message_text(message: dict | None) -> str:
    if not message:
        return ""

    content = message.get("content") or {}
    parts = content.get("parts") or []

    chunks: list[str] = []
    for part in parts:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, dict):
            text = part.get("text") or part.get("content") or ""
            if isinstance(text, str):
                chunks.append(text)

    return clean_text("\n".join(chunks))


def find_input(path: Path | None) -> Path:
    if path is not None:
        if not path.exists():
            raise SystemExit(f"Input not found: {path}")
        return path

    candidates = [
        DEFAULT_RAW_DIR / "conversations.json",
        DEFAULT_RAW_DIR / "export.zip",
        *sorted(DEFAULT_RAW_DIR.glob("*.zip")),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise SystemExit(
        "No ChatGPT export found.\n\n"
        "1. In ChatGPT: Settings → Data controls → Export data\n"
        "2. Save the zip to: data/raw/chatgpt/\n"
        "3. Run: python3 scripts/parse_chatgpt.py\n"
    )


def load_conversations(path: Path) -> list[dict]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            json_name = next(
                (n for n in names if n.endswith("conversations.json")),
                None,
            )
            if not json_name:
                raise SystemExit(
                    f"No conversations.json inside zip: {path}"
                )
            with archive.open(json_name) as handle:
                return json.load(handle)

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_pairs(conversation: dict) -> list[tuple[str, str, float | None]]:
    mapping = conversation.get("mapping") or {}
    ordered: list[tuple[float | None, str, str]] = []

    for node in mapping.values():
        message = node.get("message")
        if not message:
            continue

        role = (message.get("author") or {}).get("role")
        if role not in {"user", "assistant"}:
            continue

        text = message_text(message)
        if not text:
            continue

        create_time = message.get("create_time")
        ordered.append((create_time, role, text))

    ordered.sort(key=lambda item: item[0] or 0.0)

    pairs: list[tuple[str, str, float | None]] = []
    pending_user: str | None = None
    pending_time: float | None = None

    for create_time, role, text in ordered:
        if role == "user":
            pending_user = text
            pending_time = create_time
        elif role == "assistant" and pending_user:
            pairs.append((pending_user, text, pending_time))
            pending_user = None
            pending_time = None

    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse ChatGPT export to JSONL.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="conversations.json or OpenAI export .zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )
    args = parser.parse_args()

    input_path = find_input(args.input)
    conversations = load_conversations(input_path)

    if not isinstance(conversations, list):
        raise SystemExit("Expected conversations.json to contain a JSON array.")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with args.output.open("w", encoding="utf-8") as out:
        for conversation in conversations:
            title = conversation.get("title") or ""
            pairs = extract_pairs(conversation)

            for user_text, assistant_text, create_time in pairs:
                count += 1
                record = {
                    "id": f"chatgpt_{count:06d}",
                    "source": "chatgpt",
                    "timestamp": format_timestamp(create_time),
                    "title": title,
                    "user": user_text,
                    "assistant": assistant_text,
                }
                out.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Input:  {input_path}")
    print(f"Output: {args.output}")
    print(f"Extracted user/assistant turns: {count:,}")


if __name__ == "__main__":
    main()
