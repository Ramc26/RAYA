#!/usr/bin/env python3
"""
Inspect semantic classifications produced by RAYA.

Default input:
    data/processed/gemini_semantic.jsonl

Examples:
    python3 scripts/inspect_semantic.py
    python3 scripts/inspect_semantic.py --limit 20
    python3 scripts/inspect_semantic.py --only high
"""

import argparse
import json
from pathlib import Path

DEFAULT_INPUT = "data/processed/gemini_semantic.jsonl"


def shorten(text, limit=280):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--only",
        choices=["high", "medium", "low", "none"],
        default=None,
    )
    args = parser.parse_args()

    path = Path(args.input)

    if not path.exists():
        raise SystemExit(f"Missing file: {path}")

    records = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    shown = 0

    for record in records:
        classification = record.get(
            "semantic_classification",
            {},
        )

        value = classification.get(
            "learning_value",
            "none",
        )

        if args.only and value != args.only:
            continue

        shown += 1

        print("\n" + "=" * 80)
        print(
            f"[{shown:02}] "
            f"{value.upper()} | "
            f"id={record.get('id')}"
        )

        print(
            "Signals:",
            ", ".join(classification.get("signals", []))
            or "none",
        )

        print(
            "Learn:",
            classification.get(
                "raya_should_learn",
                False,
            ),
        )

        print(
            "Reason:",
            classification.get("reason", ""),
        )

        print(
            "User:",
            shorten(record.get("user", "")),
        )

        if shown >= args.limit:
            break

    print("\n" + "=" * 80)
    print(f"Displayed: {shown}")


if __name__ == "__main__":
    main()
