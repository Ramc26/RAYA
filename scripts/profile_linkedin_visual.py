#!/usr/bin/env python3
"""
Build a clean, single-page visual from chat export JSONL files — sized for a
LinkedIn screenshot (no console dump, no project branding).

Uses the same topic heuristics as profile_dataset.py.

Run:
    python3 scripts/profile_linkedin_visual.py

    python3 scripts/profile_linkedin_visual.py \\
        --input data/processed/gemini_raw.jsonl \\
        --input data/processed/chatgpt_raw.jsonl \\
        --output data/processed/linkedin_chat_profile.html

Open the HTML file in a browser and capture the card (1080×1080).
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import median

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from profile_dataset import classify_text, parse_timestamp, word_count  # noqa: E402

DEFAULT_INPUTS = [
    Path("data/processed/gemini_raw.jsonl"),
    Path("data/processed/chatgpt_raw.jsonl"),
]
DEFAULT_OUTPUT = Path("data/processed/linkedin_chat_profile.html")

CARD_WIDTH = 1080
CARD_HEIGHT = 1080

CATEGORY_LABELS = {
    "personal": "Personal",
    "technology": "Technology",
    "career": "Career & jobs",
    "finance": "Finance",
    "health_fitness": "Health & fitness",
    "food": "Food & cooking",
    "travel": "Travel",
    "shopping": "Shopping",
    "entertainment": "Entertainment",
    "writing_communication": "Writing & comms",
    "education": "Learning",
    "legal": "Legal & admin",
    "spirituality": "Spirituality",
    "real_estate": "Home & property",
    "automotive": "Automotive",
    "parenting": "Family",
    "productivity": "Productivity",
    "creative": "Creative work",
}


def friendly_category(name: str) -> str:
    return CATEGORY_LABELS.get(name, name.replace("_", " ").title())


def friendly_source(name: str) -> str:
    mapping = {
        "gemini": "Gemini",
        "chatgpt": "ChatGPT",
        "openai": "ChatGPT",
    }
    key = (name or "unknown").lower()
    return mapping.get(key, name.title() if name else "Unknown")


def load_records(paths: list[Path]) -> list[dict]:
    records: list[dict] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if not record.get("source"):
                    record["source"] = path.stem.replace("_raw", "")
                records.append(record)
    return records


def format_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 10_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,}"


def format_words(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(value)


def format_month_year(dt: datetime) -> str:
    return dt.strftime("%b %Y")


def compute_profile(records: list[dict]) -> dict:
    total = len(records)
    if total == 0:
        raise SystemExit("No records found. Check --input paths.")

    source_counts = Counter(r.get("source", "unknown") for r in records)

    user_word_total = 0
    user_lengths: list[int] = []
    parsed_dates: list[datetime] = []

    for record in records:
        user_text = record.get("user", "") or ""
        user_word_total += word_count(user_text)
        user_lengths.append(word_count(user_text))

        parsed = parse_timestamp(record.get("timestamp", ""))
        if parsed:
            parsed_dates.append(parsed)

    category_counts: Counter[str] = Counter()
    for record in records:
        text = (record.get("user", "") or "") + "\n" + (record.get("assistant", "") or "")
        matches = classify_text(text)
        for category, _sub in matches:
            category_counts[category] += 1

    year_counts = Counter(d.year for d in parsed_dates)

    if parsed_dates:
        start = min(parsed_dates)
        end = max(parsed_dates)
        span_days = (end - start).days
        span_label = f"{format_month_year(start)} – {format_month_year(end)}"
        if span_days >= 365:
            years = span_days / 365.25
            span_headline = f"~{years:.1f} years"
        elif span_days >= 30:
            months = span_days / 30.44
            span_headline = f"~{months:.0f} months"
        else:
            span_headline = f"{span_days} days"
    else:
        span_label = "Date range unavailable"
        span_headline = ""

    platforms = " · ".join(
        f"{friendly_source(src)} ({count:,})"
        for src, count in source_counts.most_common()
    )

    top_topics = category_counts.most_common(6)
    max_topic = top_topics[0][1] if top_topics else 1

    years_sorted = sorted(year_counts.items())

    return {
        "total": total,
        "platforms": platforms,
        "span_label": span_label,
        "span_headline": span_headline,
        "user_word_total": user_word_total,
        "median_user_words": int(median(user_lengths)) if user_lengths else 0,
        "long_prompts": sum(1 for n in user_lengths if n >= 100),
        "top_topics": top_topics,
        "max_topic": max_topic,
        "years_sorted": years_sorted,
        "max_year": max((c for _, c in years_sorted), default=1),
    }


def render_html(stats: dict) -> str:
    topic_rows = []
    for category, count in stats["top_topics"]:
        label = friendly_category(category)
        pct = count / stats["total"] * 100
        width = max(8, int(count / stats["max_topic"] * 100))
        topic_rows.append(
            f"""
            <div class="bar-row">
              <div class="bar-label">{html.escape(label)}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width:{width}%"></div>
              </div>
              <div class="bar-value">{pct:.0f}%</div>
            </div>"""
        )

    year_cells = []
    for year, count in stats["years_sorted"]:
        height = max(12, int(count / stats["max_year"] * 100))
        year_cells.append(
            f"""
            <div class="year-col">
              <div class="year-bar" style="height:{height}%"></div>
              <div class="year-label">{year}</div>
              <div class="year-count">{format_count(count)}</div>
            </div>"""
        )

    headline = "I profiled my AI chat history"
    if stats["span_headline"]:
        subtitle = f"{stats['span_headline']} · {stats['span_label']}"
    else:
        subtitle = stats["span_label"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width={CARD_WIDTH}" />
  <title>AI chat profile</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #e8e6e3;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      color: #1d2226;
    }}
    .card {{
      width: {CARD_WIDTH}px;
      height: {CARD_HEIGHT}px;
      background: linear-gradient(165deg, #ffffff 0%, #f8f9fb 55%, #eef3f8 100%);
      border-radius: 24px;
      padding: 56px 52px 48px;
      box-shadow: 0 24px 64px rgba(0, 0, 0, 0.12);
      display: flex;
      flex-direction: column;
      gap: 28px;
    }}
    h1 {{
      font-size: 42px;
      font-weight: 700;
      letter-spacing: -0.02em;
      line-height: 1.15;
      max-width: 16ch;
    }}
    .subtitle {{
      font-size: 20px;
      color: #5e5e5e;
      margin-top: 10px;
    }}
    .platforms {{
      font-size: 17px;
      color: #0a66c2;
      font-weight: 600;
      margin-top: 6px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
    }}
    .stat {{
      background: #fff;
      border: 1px solid #e0e0e0;
      border-radius: 16px;
      padding: 18px 16px;
      text-align: center;
    }}
    .stat-value {{
      font-size: 28px;
      font-weight: 700;
      color: #0a66c2;
      line-height: 1.1;
    }}
    .stat-label {{
      font-size: 13px;
      color: #666;
      margin-top: 8px;
      line-height: 1.3;
    }}
    .section-title {{
      font-size: 15px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #666;
    }}
    .bars {{ display: flex; flex-direction: column; gap: 12px; }}
    .bar-row {{
      display: grid;
      grid-template-columns: 148px 1fr 44px;
      align-items: center;
      gap: 12px;
    }}
    .bar-label {{ font-size: 15px; font-weight: 600; }}
    .bar-track {{
      height: 12px;
      background: #e8ecf1;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, #0a66c2, #378fe9);
      border-radius: 999px;
    }}
    .bar-value {{ font-size: 14px; font-weight: 600; color: #444; text-align: right; }}
    .years {{
      display: flex;
      align-items: flex-end;
      gap: 18px;
      height: 140px;
      padding-top: 8px;
    }}
    .year-col {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      justify-content: flex-end;
      gap: 6px;
    }}
    .year-bar {{
      width: 100%;
      max-width: 56px;
      background: linear-gradient(180deg, #378fe9, #0a66c2);
      border-radius: 8px 8px 4px 4px;
      min-height: 12px;
    }}
    .year-label {{ font-size: 14px; font-weight: 700; }}
    .year-count {{ font-size: 12px; color: #666; }}
  </style>
</head>
<body>
  <div class="card">
    <header>
      <h1>{html.escape(headline)}</h1>
      <p class="subtitle">{html.escape(subtitle)}</p>
      <p class="platforms">{html.escape(stats["platforms"])}</p>
    </header>

    <div class="stats">
      <div class="stat">
        <div class="stat-value">{stats["total"]:,}</div>
        <div class="stat-label">Conversations</div>
      </div>
      <div class="stat">
        <div class="stat-value">{format_words(stats["user_word_total"])}</div>
        <div class="stat-label">Words I typed</div>
      </div>
      <div class="stat">
        <div class="stat-value">{stats["median_user_words"]}</div>
        <div class="stat-label">Median prompt length (words)</div>
      </div>
      <div class="stat">
        <div class="stat-value">{stats["long_prompts"]:,}</div>
        <div class="stat-label">Prompts 100+ words</div>
      </div>
    </div>

    <section>
      <div class="section-title">What I talked about most</div>
      <div class="bars" style="margin-top:14px">
        {"".join(topic_rows)}
      </div>
    </section>

    <section>
      <div class="section-title">Activity by year</div>
      <div class="years" style="margin-top:10px">
        {"".join(year_cells) if year_cells else "<p class='subtitle'>No timestamps parsed</p>"}
      </div>
    </section>

  </div>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a LinkedIn-ready chat profile card (HTML)."
    )
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        dest="inputs",
        help="JSONL export (repeat for ChatGPT + Gemini). Skips missing files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output HTML path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    paths = args.inputs if args.inputs else DEFAULT_INPUTS
    records = load_records(paths)

    used = [p for p in paths if p.exists()]
    if not used:
        lines = ["No input JSONL files found."]
        for path in paths:
            lines.append(f"  • {path}")
            if "chatgpt" in path.name and not path.exists():
                lines.extend(
                    [
                        "    ChatGPT: export zip → data/raw/chatgpt/",
                        "    Then run: python3 scripts/parse_chatgpt.py",
                    ]
                )
            if "gemini" in path.name and not path.exists():
                lines.extend(
                    [
                        "    Gemini: run python3 scripts/parse_gemini.py",
                    ]
                )
        raise SystemExit("\n".join(lines))

    stats = compute_profile(records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(stats), encoding="utf-8")

    print(f"Wrote {args.output} ({CARD_WIDTH}×{CARD_HEIGHT})")
    print(f"Sources: {', '.join(str(p) for p in used)}")
    print(f"Conversations: {stats['total']:,}")
    print("Open in a browser and screenshot the white card for LinkedIn.")


if __name__ == "__main__":
    main()
