#!/usr/bin/env python3
"""
Select high-value Gemini conversations for the next semantic-classification stage.

Input:
    data/processed/gemini_classified.jsonl

Output:
    data/processed/gemini_candidates.jsonl

This is a candidate selector, NOT the final semantic classifier.
It preserves the original record and adds:
    candidate_score
    candidate_reasons
"""

import json
from pathlib import Path

INPUT = Path("data/processed/gemini_classified.jsonl")
OUTPUT = Path("data/processed/gemini_candidates.jsonl")

# Keep this configurable. Start with ~1,500 candidates.
TARGET_CANDIDATES = 1500

SIGNAL_WEIGHTS = {
    "correction": 10,
    "preference": 9,
    "personality": 9,
    "decision_pattern": 8,
    "memory": 7,
    "communication_style": 7,
}

TOPIC_WEIGHTS = {
    "projects": 4,
    "technology": 3,
    "career": 3,
    "productivity": 3,
    "writing_communication": 2,
    "research": 2,
    "personal": 2,
    "health_fitness": 1,
    "finance": 1,
    "food": 1,
    "travel": 1,
    "shopping": 1,
    "entertainment": 1,
}


def word_count(text):
    return len((text or "").split())


def score_record(record):
    classification = record.get("classification", {})
    signals = classification.get("signals", [])
    topics = classification.get("topics", [])
    learning_value = classification.get("learning_value", "ordinary")
    interaction_type = classification.get("interaction_type", "normal")

    user_text = record.get("user", "")
    assistant_text = record.get("assistant", "")

    score = 0
    reasons = []

    # 1. Explicit learning signals are the strongest evidence.
    for signal in signals:
        weight = SIGNAL_WEIGHTS.get(signal, 0)
        score += weight
        reasons.append(f"signal:{signal}")

    # 2. Existing classifier's learning value.
    value_bonus = {
        "high": 12,
        "medium": 6,
        "potential": 2,
        "ordinary": 0,
    }.get(learning_value, 0)
    score += value_bonus
    if value_bonus:
        reasons.append(f"value:{learning_value}")

    # 3. Useful subject areas.
    topic_score = sum(TOPIC_WEIGHTS.get(topic, 0) for topic in topics)
    score += min(topic_score, 12)

    if topics:
        useful_topics = [
            topic for topic in topics
            if topic in {"projects", "technology", "career", "productivity",
                         "personal", "writing_communication", "research"}
        ]
        if useful_topics:
            reasons.append("useful_topics:" + ",".join(useful_topics))

    # 4. Conversation depth.
    user_words = word_count(user_text)
    assistant_words = word_count(assistant_text)
    total_words = user_words + assistant_words

    if user_words >= 1000:
        score += 8
        reasons.append("very_long_user")
    elif user_words >= 500:
        score += 5
        reasons.append("long_user")
    elif user_words >= 100:
        score += 2
        reasons.append("detailed_user")

    if total_words >= 1500:
        score += 3
        reasons.append("deep_conversation")

    # 5. Communication-style examples can be valuable even when short.
    if "communication_style" in signals and user_words <= 80:
        score += 3
        reasons.append("short_style_example")

    # 6. Penalize obvious low-value/artifact records.
    quality = record.get("quality", {})
    if quality.get("generated_content"):
        score -= 5
        reasons.append("generated_artifact_penalty")

    if quality.get("duplicate"):
        score -= 8
        reasons.append("duplicate_penalty")

    if quality.get("code_heavy"):
        # Technical code can still be useful, so only a small penalty.
        score -= 2
        reasons.append("code_heavy_penalty")

    # Very short ordinary messages should rarely enter the candidate pool.
    if interaction_type == "very_short" and not signals:
        score -= 6
        reasons.append("very_short_penalty")

    # Empty/near-empty assistant replies are not useful for SFT.
    if assistant_words < 10:
        score -= 8
        reasons.append("short_assistant_penalty")

    return score, reasons


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing input: {INPUT}")

    records = []
    with INPUT.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    scored = []
    for record in records:
        score, reasons = score_record(record)
        item = dict(record)
        item["candidate_score"] = score
        item["candidate_reasons"] = reasons
        scored.append(item)

    # Stable sorting: score first, original id second.
    scored.sort(
        key=lambda r: (-r["candidate_score"], r.get("id", ""))
    )

    candidates = scored[:TARGET_CANDIDATES]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        for record in candidates:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("Candidate selection complete")
    print(f"Input records: {len(records):,}")
    print(f"Target candidates: {TARGET_CANDIDATES:,}")
    print(f"Output candidates: {len(candidates):,}")

    if candidates:
        scores = [r["candidate_score"] for r in candidates]
        print(f"Score range: {min(scores)} to {max(scores)}")
        print(f"Output: {OUTPUT}")

        print("\nTop 10 candidates:")
        for i, record in enumerate(candidates[:10], 1):
            user = " ".join(record.get("user", "").split())
            preview = user[:120] + ("..." if len(user) > 120 else "")
            print(
                f"{i:2}. score={record['candidate_score']:>3} "
                f"id={record.get('id')} | {preview}"
            )


if __name__ == "__main__":
    main()
