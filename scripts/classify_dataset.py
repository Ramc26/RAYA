import json
import re
from collections import Counter
from pathlib import Path


INPUT = Path("data/processed/gemini_clean.jsonl")
OUTPUT = Path("data/processed/gemini_classified.jsonl")


# ============================================================
# TOPIC TAXONOMY
# ============================================================

TOPICS = {
    "technology": [
        "python", "javascript", "typescript", "golang", "programming",
        "coding", "code", "django", "flask", "fastapi", "docker",
        "kubernetes", "k8s", "api", "backend", "frontend", "react",
        "database", "postgres", "postgresql", "mongodb", "redis",
        "sql", "aws", "azure", "gcp", "cloud", "github", "git",
        "linux", "macos", "server", "deployment", "devops",
        "machine learning", "deep learning", "llm", "llama", "gemini",
        "openai", "claude", "transformer", "lora", "peft",
        "hugging face", "agent", "agentic", "mcp", "model context protocol",
        "fastmcp", "system design", "architecture", "software"
    ],

    "career": [
        "job", "jobs", "hiring", "career", "resume", "cv", "ats",
        "interview", "salary", "lpa", "ctc", "compensation",
        "freelance", "freelancing", "client", "contract",
        "linkedin", "promotion", "manager", "workplace",
        "experience", "skills", "learning", "course", "certification"
    ],

    "finance": [
        "stock", "stocks", "share", "shares", "invest", "investment",
        "portfolio", "mutual fund", "sip", "ipo", "dividend",
        "nifty", "sensex", "nasdaq", "market", "etf",
        "capital gains", "tax", "trading", "broker", "groww",
        "indmoney", "bank", "banking", "loan", "credit card"
    ],

    "health_fitness": [
        "gym", "workout", "exercise", "muscle", "protein",
        "calories", "diet", "nutrition", "weight", "fat loss",
        "sleep", "insomnia", "doctor", "medicine", "vitamin",
        "fever", "pain", "itching", "health", "wellness"
    ],

    "food": [
        "recipe", "cook", "cooking", "chicken", "rice", "oats",
        "egg", "eggs", "milk", "curd", "breakfast", "lunch",
        "dinner", "meal", "food", "air fryer", "ingredient"
    ],

    "travel": [
        "trip", "travel", "tour", "vacation", "flight", "airport",
        "hotel", "resort", "itinerary", "route", "visit",
        "temple", "darshan", "tirumala", "warangal", "ramappa"
    ],

    "shopping": [
        "buy", "buying", "purchase", "shopping", "worth buying",
        "price", "amazon", "flipkart", "watch", "casio", "fossil",
        "diesel", "titan", "iphone", "macbook", "camera", "canon",
        "air fryer", "laptop", "phone", "headphones", "compare",
        "comparison", "vs", "versus"
    ],

    "entertainment": [
        "movie", "film", "marvel", "mcu", "comic", "comics",
        "dc", "game", "gaming", "playstation", "xbox",
        "music", "song", "spotify", "book", "novel"
    ],

    "writing_communication": [
        "rewrite", "rephrase", "paraphrase", "grammar", "email",
        "mail", "message", "whatsapp", "reply", "response",
        "linkedin post", "caption", "letter", "draft", "writing"
    ],

    "projects": [
        "raya", "sam agent", "sam", "agent eval", "evaluation studio",
        "rambuilds", "freelance page", "website", "seo", "geo", "aeo",
        "sitemap", "robots.txt", "project", "poc", "prototype"
    ],

    "research": [
        "research", "science", "physics", "biology", "chemistry",
        "space", "nasa", "planet", "mars", "moon", "alien",
        "history", "historical", "mythology", "puran", "puranas",
        "why does", "how does", "explain", "latest", "current", "news"
    ],

    "productivity": [
        "plan", "planning", "schedule", "calendar", "meeting",
        "appointment", "routine", "organize", "organization",
        "todo", "task", "checklist", "automation", "reminder"
    ],

    "personal": [
        "my preference", "i prefer", "i like", "i don't like",
        "i dont like", "i want", "i don't want", "i dont want",
        "my style", "my personality", "about me", "remember me",
        "my family", "my friend", "my sister", "my parents",
        "my routine", "my life"
    ],
}


# ============================================================
# LEARNING SIGNALS
#
# These are deliberately conservative.
# We do NOT classify a conversation as a correction merely
# because the word "actually" appears somewhere.
# ============================================================

SIGNAL_PATTERNS = {
    "correction": [
        r"\bthat's not what i meant\b",
        r"\bthat is not what i meant\b",
        r"\bnot what i meant\b",
        r"\byou misunderstood\b",
        r"\bthat's wrong\b",
        r"\bthat is wrong\b",
        r"\bthis is wrong\b",
        r"\bincorrect\b",
        r"\bnot like that\b",
        r"\bno,?\s+that's\b",
        r"\bno,?\s+that is\b",
        r"\bkeep it shorter\b",
        r"\btoo long\b",
        r"\btoo much\b",
        r"\bdon't do that\b",
        r"\bdont do that\b",
    ],

    "preference": [
        r"\bi prefer\b",
        r"\bi don't like\b",
        r"\bi dont like\b",
        r"\bmy preference\b",
        r"\bi want you to\b",
        r"\bi don't want you to\b",
        r"\bi dont want you to\b",
        r"\balways use\b",
        r"\bdon't use\b",
        r"\bdont use\b",
        r"\bfrom now on\b",
        r"\bgoing forward\b",
    ],

    "personality": [
        r"\bmy personality\b",
        r"\bthat's how i am\b",
        r"\bthat is how i am\b",
        r"\bthis is how i think\b",
        r"\bi usually\b",
        r"\bi tend to\b",
        r"\bmy style\b",
    ],

    "decision_pattern": [
        r"\bshould i\b",
        r"\bwhich should i\b",
        r"\bwhat should i\b",
        r"\bhelp me decide\b",
        r"\bwhich one should\b",
        r"\bwhich one do you think\b",
        r"\bis it worth\b",
        r"\bwhat would you choose\b",
    ],

    "memory": [
        r"\bremember that\b",
        r"\bremember this\b",
        r"\bdon't forget\b",
        r"\bdont forget\b",
        r"\bsave this\b",
        r"\bkeep this in mind\b",
        r"\byou should remember\b",
    ],

    "communication_style": [
        r"\bkeep it short\b",
        r"\bkeep it simple\b",
        r"\bbe concise\b",
        r"\bshort answer\b",
        r"\bjust give me\b",
        r"\bno explanation\b",
        r"\bwith reasoning\b",
        r"\bexplain simply\b",
        r"\bmake it simple\b",
    ],
}


def normalize(text):
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def word_count(text):
    return len(re.findall(r"\b\w+\b", text or ""))


def match_topics(text):
    """
    Topic matching is intentionally broad.
    A conversation may have multiple topics.
    """
    text = normalize(text)
    matches = []

    for topic, keywords in TOPICS.items():

        for keyword in keywords:

            # Word-boundary matching for short keywords.
            if len(keyword.split()) == 1:
                pattern = rf"\b{re.escape(keyword)}\b"

                if re.search(pattern, text):
                    matches.append(topic)
                    break

            else:
                if keyword in text:
                    matches.append(topic)
                    break

    return matches


def match_signals(user_text):
    """
    Detect learning signals primarily from the user's message.
    """
    text = normalize(user_text)
    matches = []

    for signal, patterns in SIGNAL_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text):
                matches.append(signal)
                break

    return matches


def classify_record(record):

    user = record.get("user", "")
    assistant = record.get("assistant", "")

    combined = f"{user}\n{assistant}"

    topics = match_topics(combined)
    signals = match_signals(user)

    metadata = record.get("metadata", {})

    # --------------------------------------------------------
    # Technical indicators
    # --------------------------------------------------------

    technical = bool(
        metadata.get("contains_code")
        or metadata.get("contains_html")
    )

    # --------------------------------------------------------
    # Conversation characteristics
    # --------------------------------------------------------

    user_words = word_count(user)
    assistant_words = word_count(assistant)

    if user_words <= 5:
        interaction_type = "very_short"

    elif user_words >= 1000:
        interaction_type = "long_form"

    elif user_words >= 500:
        interaction_type = "detailed"

    else:
        interaction_type = "normal"

    # --------------------------------------------------------
    # Learning value
    # --------------------------------------------------------

    if signals:
        learning_value = "high"

    elif technical and "projects" in topics:
        learning_value = "medium"

    elif len(user) >= 100:
        learning_value = "potential"

    else:
        learning_value = "ordinary"

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    classification = {
        "topics": topics,
        "signals": signals,
        "learning_value": learning_value,
        "interaction_type": interaction_type,
        "technical": technical,
    }

    return classification


def main():

    records = []

    with INPUT.open("r", encoding="utf-8") as f:

        for line in f:

            if line.strip():
                records.append(json.loads(line))

    print("\n" + "=" * 70)
    print("RAYA DATASET CLASSIFIER v0.1")
    print("=" * 70)

    print(f"\nInput records: {len(records):,}")

    classified = []

    topic_counts = Counter()
    signal_counts = Counter()
    learning_counts = Counter()
    interaction_counts = Counter()

    for record in records:

        classification = classify_record(record)

        output = dict(record)
        output["classification"] = classification

        classified.append(output)

        for topic in classification["topics"]:
            topic_counts[topic] += 1

        for signal in classification["signals"]:
            signal_counts[signal] += 1

        learning_counts[classification["learning_value"]] += 1
        interaction_counts[classification["interaction_type"]] += 1

    # --------------------------------------------------------
    # WRITE
    # --------------------------------------------------------

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:

        for record in classified:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                ) + "\n"
            )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print("\n--- TOPICS ---")

    for topic, count in topic_counts.most_common():

        percentage = count / len(records) * 100

        print(
            f"{topic:25} "
            f"{count:5,} "
            f"({percentage:5.1f}%)"
        )

    print("\n--- LEARNING SIGNALS ---")

    for signal, count in signal_counts.most_common():

        percentage = count / len(records) * 100

        print(
            f"{signal:25} "
            f"{count:5,} "
            f"({percentage:5.1f}%)"
        )

    print("\n--- LEARNING VALUE ---")

    for value, count in learning_counts.most_common():

        percentage = count / len(records) * 100

        print(
            f"{value:25} "
            f"{count:5,} "
            f"({percentage:5.1f}%)"
        )

    print("\n--- INTERACTION TYPE ---")

    for value, count in interaction_counts.most_common():

        percentage = count / len(records) * 100

        print(
            f"{value:25} "
            f"{count:5,} "
            f"({percentage:5.1f}%)"
        )

    # --------------------------------------------------------
    # SIGNAL SAMPLES
    # --------------------------------------------------------

    print("\n--- LEARNING SIGNAL SAMPLES ---")

    for signal in signal_counts:

        print(f"\n### {signal}")

        shown = 0

        for record in classified:

            if signal not in record["classification"]["signals"]:
                continue

            user = record["user"].replace("\n", " ")

            print(f"- {user[:350]}")

            shown += 1

            if shown >= 5:
                break

    # --------------------------------------------------------
    # TOPIC SAMPLES
    # --------------------------------------------------------

    print("\n--- TOPIC SAMPLES ---")

    for topic in topic_counts:

        print(f"\n### {topic}")

        shown = 0

        for record in classified:

            if topic not in record["classification"]["topics"]:
                continue

            user = record["user"].replace("\n", " ")

            print(f"- {user[:250]}")

            shown += 1

            if shown >= 3:
                break

    print("\n" + "=" * 70)
    print("CLASSIFICATION COMPLETE")
    print("=" * 70)

    print(f"\nOutput:")
    print(f"  {OUTPUT}")

    print("\nIMPORTANT:")
    print("This is a heuristic annotation layer.")
    print("Do NOT train RAYA from these classifications yet.")
    print("Review the results first.")


if __name__ == "__main__":
    main()