#!/usr/bin/env python3
"""
RAYA candidate prefilter.

Removes/flags obvious technical artifacts before semantic classification.

Input:
    data/processed/gemini_candidates.jsonl

Output:
    data/processed/gemini_semantic_candidates.jsonl

Also writes:
    data/processed/gemini_filtered_out.jsonl

The original candidate file is never modified.

Usage:
    python3 scripts/filter_candidates.py
    python3 scripts/filter_candidates.py --limit 1500
"""

import argparse
import json
import re
from pathlib import Path

DEFAULT_INPUT = "data/processed/gemini_candidates.jsonl"
DEFAULT_OUTPUT = "data/processed/gemini_semantic_candidates.jsonl"
DEFAULT_FILTERED = "data/processed/gemini_filtered_out.jsonl"

# Strong technical/artifact indicators.
CODE_PATTERNS = [
    r"^\s*(from|import)\s+\w+",
    r"^\s*(def|class)\s+\w+",
    r"^\s*(async\s+def)\s+\w+",
    r"^\s*#!/",
    r"\bTraceback \(most recent call last\)",
    r"\bHTTP/\d(?:\.\d)?\s+\d{3}",
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+/\S*",
    r"\b127\.0\.0\.1:\d+",
    r"\buvicorn\b",
    r"\bINFO:\s+\S+",
    r"\bERROR:\s+\S+",
    r"\bDEBUG:\s+\S+",
    r"\bException:\s*",
    r"\bValidationError\b",
    r"\bFile \"[^\"]+\", line \d+",
]

STRUCTURED_CODE_MARKERS = [
    "```python",
    "```javascript",
    "```typescript",
    "```bash",
    "```json",
    "```yaml",
    "```dockerfile",
    "<script>",
    "</script>",
    "curl --location",
    "npm install",
    "pip install",
    "docker compose",
    "dockerfile",
    "requirements.txt",
    "package.json",
]

TECHNICAL_CONTEXT = [
    "api",
    "code",
    "python",
    "javascript",
    "typescript",
    "docker",
    "fastapi",
    "django",
    "flask",
    "streamlit",
    "mcp",
    "server",
    "endpoint",
    "stack trace",
    "traceback",
    "deployment",
    "production",
    "database",
    "postgres",
    "sql",
    "github",
    "terminal",
    "uv run",
    "curl",
]

# Explicit personal-learning language can rescue a technical conversation.
PERSONAL_SIGNALS = [
    r"\bi prefer\b",
    r"\bi like\b",
    r"\bi don't like\b",
    r"\bi dislike\b",
    r"\bi want\b",
    r"\bi need\b",
    r"\bmy goal\b",
    r"\bmy preference\b",
    r"\bfor me\b",
    r"\bfrom now on\b",
    r"\bremember that\b",
    r"\bplease remember\b",
    r"\bi always\b",
    r"\bi usually\b",
    r"\bi tend to\b",
    r"\bi'm trying to\b",
    r"\bi am trying to\b",
    r"\bmy personality\b",
    r"\bmy style\b",
    r"\bkeep it\b",
    r"\bmake it\b",
    r"\bdon't make it\b",
    r"\bdo not make it\b",
    r"\bthat's not what i meant\b",
    r"\bthat is not what i meant\b",
    r"\bshorter\b",
    r"\bmore concise\b",
    r"\bbe concise\b",
]

# Technical work can still be valuable when the user is explicitly
# defining a recurring project/engineering preference or requirement.
PROJECT_SIGNAL_PATTERNS = [
    r"\bwe need\b",
    r"\bwe should\b",
    r"\bi decided\b",
    r"\bi chose\b",
    r"\bi want to build\b",
    r"\bi'm building\b",
    r"\bi am building\b",
    r"\bmy project\b",
    r"\bour project\b",
]


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def matches_any(text, patterns):
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def count_code_signals(text):
    lowered = text.lower()
    score = 0

    for pattern in CODE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            score += 1

    for marker in STRUCTURED_CODE_MARKERS:
        if marker in lowered:
            score += 1

    return score


def count_personal_signals(text):
    return sum(
        1
        for pattern in PERSONAL_SIGNALS
        if re.search(pattern, text, re.IGNORECASE)
    )


def count_project_signals(text):
    return sum(
        1
        for pattern in PROJECT_SIGNAL_PATTERNS
        if re.search(pattern, text, re.IGNORECASE)
    )


def classify(record):
    user = normalize(record.get("user", ""))
    assistant = normalize(record.get("assistant", ""))

    combined = f"{user}\n{assistant}"

    code_score = count_code_signals(user)
    personal_score = count_personal_signals(user)
    project_score = count_project_signals(user)

    technical_hits = sum(
        1
        for term in TECHNICAL_CONTEXT
        if term in user.lower()
    )

    # Very strong artifact evidence.
    if code_score >= 3:
        if personal_score == 0 and project_score == 0:
            return "filtered", [
                "strong_code_artifact",
                f"code_signals={code_score}",
            ]

    # Obvious logs / dumps.
    log_patterns = [
        r"\bINFO:\s+\S+",
        r"\bDEBUG:\s+\S+",
        r"\bGET\s+/\S+",
        r"\bPOST\s+/\S+",
        r"\b127\.0\.0\.1:\d+",
        r"Traceback \(most recent call last\)",
    ]

    log_hits = sum(
        1
        for pattern in log_patterns
        if re.search(pattern, user, re.IGNORECASE)
    )

    if log_hits >= 2 and personal_score == 0:
        return "filtered", [
            "runtime_log",
            f"log_signals={log_hits}",
        ]

    # Huge code-only messages without personal/project intent.
    if len(user) > 2500 and code_score >= 2:
        if personal_score == 0 and project_score == 0:
            return "filtered", [
                "large_technical_dump",
                f"code_signals={code_score}",
            ]

    # Technical conversation but explicit personal/project intent:
    # keep it for semantic review.
    if personal_score >= 1:
        return "keep", [
            "explicit_personal_signal",
            f"personal_signals={personal_score}",
        ]

    if project_score >= 1 and technical_hits >= 1:
        return "keep", [
            "project_intent",
            f"project_signals={project_score}",
        ]

    # Technical-looking records with no explicit personal signal:
    # keep borderline cases rather than throwing them away.
    if technical_hits >= 3 and code_score >= 1:
        return "filtered", [
            "technical_artifact_likely",
            f"technical_hits={technical_hits}",
            f"code_signals={code_score}",
        ]

    return "keep", ["not_obviously_artifact"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--filtered", default=DEFAULT_FILTERED)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    filtered_path = Path(args.filtered)

    if not input_path.exists():
        raise SystemExit(f"Missing input: {input_path}")

    records = []

    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if args.limit is not None:
        records = records[:args.limit]

    kept = 0
    filtered = 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with (
        output_path.open("w", encoding="utf-8") as keep_file,
        filtered_path.open("w", encoding="utf-8") as filtered_file,
    ):
        for record in records:
            status, reasons = classify(record)

            result = dict(record)
            result["prefilter"] = {
                "status": status,
                "reasons": reasons,
            }

            if status == "keep":
                keep_file.write(
                    json.dumps(result, ensure_ascii=False) + "\n"
                )
                kept += 1
            else:
                filtered_file.write(
                    json.dumps(result, ensure_ascii=False) + "\n"
                )
                filtered += 1

    print("\nCandidate prefilter complete")
    print(f"Input:             {input_path}")
    print(f"Kept:              {kept:,}")
    print(f"Filtered:          {filtered:,}")
    print(f"Total processed:   {len(records):,}")
    print(f"Semantic input:    {output_path}")
    print(f"Filtered records:  {filtered_path}")

    if records:
        print(
            f"Keep rate:         "
            f"{kept / len(records) * 100:.1f}%"
        )


if __name__ == "__main__":
    main()
