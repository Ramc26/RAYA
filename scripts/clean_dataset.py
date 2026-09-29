import json
import re
from pathlib import Path
from collections import Counter


INPUT = Path("data/processed/gemini_raw.jsonl")
OUTPUT = Path("data/processed/gemini_clean.jsonl")


def normalize_text(text):
    """Normalize whitespace without changing the actual content."""
    if not text:
        return ""

    text = text.replace("\u00a0", " ")
    text = text.replace("\u202f", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def is_metadata_timestamp(value):
    """Detect Gemini activity metadata that was mistakenly parsed as a timestamp."""

    if not value:
        return False

    metadata_patterns = [
        r"^\d+ generated image[s]?\.$",
        r"^\d+ generated file[s]?\.$",
        r"^Attached \d+ file[s]?\.$",
        r"^LinkedIn Post Generator was used in this chat\.$",
        r"^Sam - PivotPal was used in this chat\.$",
    ]

    return any(
        re.match(pattern, value.strip(), re.IGNORECASE)
        for pattern in metadata_patterns
    )


def contains_code(text):
    """Heuristic detection of programming/code-heavy content."""

    if not text:
        return False

    indicators = [
        "```",
        "def ",
        "class ",
        "import ",
        "from ",
        "return ",
        "const ",
        "function ",
        "async ",
        "await ",
        "json",
        "yaml",
        "dockerfile",
        "stack trace",
        "traceback",
        "exception",
        "npm ",
        "pip ",
        "kubectl ",
        "git ",
    ]

    text_lower = text.lower()

    matches = sum(
        1 for indicator in indicators
        if indicator in text_lower
    )

    # A few strong signals are enough.
    return matches >= 2


def contains_html(text):
    """Detect HTML-heavy content."""

    if not text:
        return False

    html_patterns = [
        r"<div[\s>]",
        r"<span[\s>]",
        r"<p[\s>]",
        r"<html[\s>]",
        r"<body[\s>]",
        r"<table[\s>]",
        r"</div>",
        r"</span>",
        r"</p>",
    ]

    matches = sum(
        1 for pattern in html_patterns
        if re.search(pattern, text, re.IGNORECASE)
    )

    return matches >= 2


def looks_like_generated_content(text):
    """
    Detect obvious generated/artifact-heavy entries.

    We DO NOT remove these.
    We only mark them so the classifier can decide later.
    """

    if not text:
        return False

    indicators = [
        "generated image",
        "generated file",
        "image prompt",
        "create an image",
        "photorealistic",
        "oil painting",
        "yaml:",
        "json:",
        "html:",
    ]

    text_lower = text.lower()

    return any(indicator in text_lower for indicator in indicators)


def main():

    records = []

    with INPUT.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print("\n" + "=" * 70)
    print("RAYA DATASET CLEANER v0.1")
    print("=" * 70)

    print(f"\nInput records: {len(records):,}")

    cleaned = []

    stats = Counter()

    seen = set()

    for record in records:

        user = normalize_text(record.get("user", ""))
        assistant = normalize_text(record.get("assistant", ""))

        # ----------------------------------------------------
        # EMPTY USER
        # ----------------------------------------------------

        if not user:
            stats["empty_user"] += 1
            continue

        # ----------------------------------------------------
        # EMPTY ASSISTANT
        # ----------------------------------------------------

        if not assistant:
            stats["empty_assistant"] += 1
            continue

        # ----------------------------------------------------
        # DUPLICATE DETECTION
        # ----------------------------------------------------

        duplicate_key = (
            user.lower(),
            assistant.lower(),
        )

        is_duplicate = duplicate_key in seen

        if is_duplicate:
            stats["duplicates"] += 1

        seen.add(duplicate_key)

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        timestamp = record.get("timestamp", "")

        timestamp_is_metadata = is_metadata_timestamp(timestamp)

        if timestamp_is_metadata:
            stats["metadata_timestamps"] += 1

        # ----------------------------------------------------
        # CONTENT FLAGS
        # ----------------------------------------------------

        combined = user + "\n" + assistant

        code_flag = contains_code(combined)
        html_flag = contains_html(combined)
        generated_flag = looks_like_generated_content(combined)

        if code_flag:
            stats["contains_code"] += 1

        if html_flag:
            stats["contains_html"] += 1

        if generated_flag:
            stats["generated_content"] += 1

        # ----------------------------------------------------
        # QUALITY
        # ----------------------------------------------------

        if is_duplicate:
            quality = "duplicate"

        elif timestamp_is_metadata:
            quality = "metadata_timestamp"

        elif generated_flag:
            quality = "generated_content"

        elif code_flag or html_flag:
            quality = "technical"

        else:
            quality = "normal"

        # ----------------------------------------------------
        # CREATE CLEAN RECORD
        # ----------------------------------------------------

        clean_record = {
            "id": record.get("id"),
            "source": record.get("source"),
            "timestamp": None if timestamp_is_metadata else timestamp,
            "user": user,
            "assistant": assistant,

            "metadata": {
                "quality": quality,
                "is_duplicate": is_duplicate,
                "contains_code": code_flag,
                "contains_html": html_flag,
                "generated_content": generated_flag,
                "timestamp_is_metadata": timestamp_is_metadata,
            },
        }

        cleaned.append(clean_record)

    # --------------------------------------------------------
    # WRITE OUTPUT
    # --------------------------------------------------------

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        for record in cleaned:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                ) + "\n"
            )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print("\n--- CLEANING RESULTS ---")

    print(f"Output records       : {len(cleaned):,}")
    print(f"Removed empty user   : {stats['empty_user']:,}")
    print(f"Removed empty reply  : {stats['empty_assistant']:,}")
    print(f"Duplicate records    : {stats['duplicates']:,}")

    print("\n--- CONTENT FLAGS ---")

    print(f"Code-heavy           : {stats['contains_code']:,}")
    print(f"HTML-heavy            : {stats['contains_html']:,}")
    print(f"Generated/artifact    : {stats['generated_content']:,}")

    print("\n--- METADATA ---")

    print(
        f"Metadata timestamps  : "
        f"{stats['metadata_timestamps']:,}"
    )

    # --------------------------------------------------------
    # QUALITY DISTRIBUTION
    # --------------------------------------------------------

    quality_counts = Counter(
        record["metadata"]["quality"]
        for record in cleaned
    )

    print("\n--- QUALITY DISTRIBUTION ---")

    for quality, count in quality_counts.most_common():
        percentage = count / len(cleaned) * 100
        print(
            f"{quality:22} "
            f"{count:5,} "
            f"({percentage:5.1f}%)"
        )

    print("\nOutput:")
    print(f"  {OUTPUT}")

    print("\nRaw dataset was NOT modified.")

    print("\n" + "=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()