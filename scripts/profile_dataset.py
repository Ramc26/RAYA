import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median


INPUT = Path("data/processed/gemini_raw.jsonl")


# ============================================================
# TAXONOMY
# ============================================================

TAXONOMY = {
    "personal": {
        "personality": [
            "personality", "character", "behavior", "nature", "habit",
            "introvert", "extrovert", "mindset"
        ],
        "preferences": [
            "prefer", "preference", "like", "dislike", "favorite",
            "favourite", "i want", "i don't want", "dont want"
        ],
        "communication_style": [
            "keep it short", "shorter", "concise", "brief", "simple",
            "explain", "tone", "wording", "rewrite", "message"
        ],
        "lifestyle": [
            "routine", "daily", "morning", "night", "lifestyle",
            "schedule", "habit"
        ],
        "relationships": [
            "friend", "girlfriend", "family", "sister", "brother",
            "parents", "relationship", "wife", "marriage"
        ],
        "memory": [
            "remember", "forget", "save this", "my name", "about me",
            "you know me"
        ],
    },

    "technology": {
        "programming": [
            "python", "javascript", "typescript", "golang", "go lang",
            "java", "c++", "rust", "programming", "coding", "code"
        ],
        "web_development": [
            "html", "css", "bootstrap", "jquery", "react", "next.js",
            "frontend", "web app", "website"
        ],
        "backend": [
            "django", "flask", "fastapi", "backend", "rest api",
            "microservice", "api"
        ],
        "databases": [
            "postgres", "postgresql", "mysql", "mongodb", "redis",
            "database", "sql", "qdrant", "milvus", "elasticsearch"
        ],
        "devops": [
            "docker", "kubernetes", "k8s", "helm", "container",
            "deployment", "ci/cd", "pipeline"
        ],
        "cloud": [
            "aws", "azure", "gcp", "google cloud", "cloud",
            "vercel", "serverless"
        ],
        "ai_ml": [
            "machine learning", "deep learning", "neural network",
            "tensorflow", "pytorch", "model", "ml"
        ],
        "llm": [
            "llm", "large language model", "llama", "gemini",
            "openai", "claude", "transformer", "fine tuning",
            "fine-tuning", "lora", "peft", "hugging face"
        ],
        "agents": [
            "agent", "agentic", "agent framework", "agent harness",
            "tool calling", "function calling"
        ],
        "mcp": [
            "mcp", "model context protocol", "fastmcp", "mcp server",
            "mcp gateway"
        ],
        "cybersecurity": [
            "security", "cybersecurity", "snyk", "aikido",
            "vulnerability", "penetration"
        ],
        "system_design": [
            "system design", "architecture", "distributed system",
            "scalability", "high availability", "design pattern"
        ],
        "troubleshooting": [
            "error", "exception", "bug", "issue", "not working",
            "failed", "failure", "debug", "troubleshoot"
        ],
    },

    "career": {
        "jobs": [
            "job", "hiring", "company", "role", "position",
            "job search", "job opening"
        ],
        "resume": [
            "resume", "cv", "ats", "application"
        ],
        "interviews": [
            "interview", "technical round", "hr round"
        ],
        "salary": [
            "salary", "lpa", "compensation", "package", "ctc"
        ],
        "freelancing": [
            "freelance", "freelancing", "client", "contract"
        ],
        "linkedin": [
            "linkedin", "profile", "headline", "about section"
        ],
        "learning": [
            "learn", "learning", "course", "study", "roadmap",
            "tutorial", "certification"
        ],
        "workplace": [
            "manager", "colleague", "office", "workplace",
            "company policy", "team"
        ],
    },

    "finance": {
        "stocks": [
            "stock", "stocks", "share", "shares", "equity"
        ],
        "investing": [
            "invest", "investment", "portfolio", "investing"
        ],
        "mutual_funds": [
            "mutual fund", "mf", "sip", "index fund"
        ],
        "ipo": [
            "ipo", "initial public offering"
        ],
        "dividends": [
            "dividend", "interim dividend", "final dividend"
        ],
        "taxes": [
            "tax", "taxes", "capital gains", "gst", "itr"
        ],
        "banking": [
            "bank", "banking", "loan", "credit card", "upi"
        ],
        "personal_finance": [
            "savings", "budget", "money", "income", "expense"
        ],
        "markets": [
            "market", "nifty", "sensex", "nasdaq", "dow jones"
        ],
    },

    "health_fitness": {
        "gym": [
            "gym", "workout", "training", "muscle", "bodybuilding"
        ],
        "exercise": [
            "exercise", "cardio", "treadmill", "squat", "bench press",
            "lat pull", "crunch", "pushup", "pullup"
        ],
        "nutrition": [
            "protein", "calories", "macro", "nutrition"
        ],
        "diet": [
            "diet", "meal plan", "weight loss", "fat loss"
        ],
        "sleep": [
            "sleep", "insomnia", "sleeping", "wake up"
        ],
        "medical": [
            "doctor", "symptom", "medicine", "vitamin", "fever",
            "pain", "itching"
        ],
        "wellness": [
            "health", "wellness", "stress", "mental health"
        ],
    },

    "food": {
        "recipes": [
            "recipe", "how to cook", "ingredients"
        ],
        "cooking": [
            "cook", "cooking", "boil", "fry", "bake", "air fry"
        ],
        "ingredients": [
            "chicken", "rice", "oats", "egg", "milk", "curd",
            "vegetable", "paneer"
        ],
        "groceries": [
            "grocery", "groceries", "buy", "shopping list"
        ],
        "meal_planning": [
            "breakfast", "lunch", "dinner", "meal prep", "meal plan"
        ],
    },

    "travel": {
        "trips": [
            "trip", "travel", "tour", "vacation", "journey"
        ],
        "hotels": [
            "hotel", "resort", "stay", "room"
        ],
        "flights": [
            "flight", "airport", "airline", "boarding"
        ],
        "places": [
            "place", "visit", "tourist", "attraction"
        ],
        "temples": [
            "temple", "darshan", "puja", "tirumala", "ramappa",
            "bhadrakali"
        ],
        "itineraries": [
            "itinerary", "route", "plan a trip", "travel plan"
        ],
    },

    "shopping": {
        "electronics": [
            "iphone", "macbook", "laptop", "phone", "earbuds",
            "headphones", "router"
        ],
        "watches": [
            "watch", "casio", "fossil", "diesel", "titan",
            "armani exchange", "seiko"
        ],
        "clothing": [
            "shirt", "pants", "shoe", "clothing", "jacket"
        ],
        "appliances": [
            "air fryer", "fridge", "washing machine", "appliance"
        ],
        "cameras": [
            "camera", "canon", "dslr", "lens", "photography"
        ],
        "product_comparison": [
            "which should i buy", "compare", "comparison", "worth buying",
            "best", "alternative", "vs", "versus"
        ],
    },

    "entertainment": {
        "movies": [
            "movie", "film", "marvel", "mcu", "actor"
        ],
        "comics": [
            "comic", "comics", "marvel comics", "dc comics"
        ],
        "games": [
            "game", "gaming", "playstation", "xbox", "nintendo"
        ],
        "music": [
            "song", "music", "album", "spotify"
        ],
        "books": [
            "book", "novel", "author", "reading"
        ],
    },

    "writing_communication": {
        "rewriting": [
            "rewrite", "rephrase", "paraphrase", "correct this",
            "grammar"
        ],
        "emails": [
            "email", "mail", "grievance", "complaint"
        ],
        "messages": [
            "text message", "whatsapp", "reply", "response"
        ],
        "social_media": [
            "instagram", "twitter", "x.com", "social media", "caption"
        ],
        "linkedin": [
            "linkedin post", "linkedin headline", "linkedin about"
        ],
        "creative_writing": [
            "story", "poem", "creative writing", "joke"
        ],
    },

    "projects": {
        "raya": [
            "raya", "personal ai", "personal model", "personal assistant"
        ],
        "sam": [
            "sam agent", "sam", "inbox manager", "calendar manager"
        ],
        "agent_eval": [
            "agent eval", "evaluation studio", "eval studio"
        ],
        "freelance": [
            "rambuilds", "freelance page", "freelance website"
        ],
        "websites": [
            "website", "seo", "geo", "aeo", "sitemap", "robots.txt"
        ],
    },

    "research": {
        "science": [
            "science", "physics", "biology", "chemistry"
        ],
        "space": [
            "space", "nasa", "planet", "mars", "moon", "alien",
            "extraterrestrial", "europa"
        ],
        "history": [
            "history", "historical", "ancient", "empire"
        ],
        "mythology": [
            "mythology", "mythological", "puran", "puranas",
            "shiva", "vishnu", "krishna"
        ],
        "general_knowledge": [
            "what is", "why does", "how does", "explain"
        ],
        "current_events": [
            "today", "latest", "recent", "current", "news"
        ],
    },

    "productivity": {
        "planning": [
            "plan", "planning", "schedule", "organize"
        ],
        "automation": [
            "automation", "automate", "reminder", "scheduled"
        ],
        "calendar": [
            "calendar", "meeting", "appointment"
        ],
        "routines": [
            "routine", "daily routine", "weekly routine"
        ],
        "organization": [
            "organize", "organization", "todo", "task", "checklist"
        ],
    },
}


# ============================================================
# LEARNING SIGNALS
# ============================================================

LEARNING_SIGNALS = {
    "correction": [
        "that's not",
        "that is not",
        "not what i meant",
        "i meant",
        "wrong",
        "incorrect",
        "you misunderstood",
        "misunderstood",
        "no, ",
        "actually",
        "don't do that",
        "dont do that",
        "not like that",
        "too long",
        "too much",
        "keep it shorter",
        "make it shorter",
    ],

    "preference": [
        "i prefer",
        "i like",
        "i don't like",
        "i dont like",
        "my preference",
        "i want",
        "i don't want",
        "i dont want",
        "always use",
        "don't use",
        "dont use",
    ],

    "personality": [
        "that's how i am",
        "this is how i think",
        "i usually",
        "i tend to",
        "my personality",
        "my style",
        "i think",
        "i feel",
    ],

    "decision": [
        "should i",
        "which should i",
        "what should i",
        "would you choose",
        "help me decide",
        "which one",
        "should i buy",
        "is it worth",
    ],

    "memory": [
        "remember that",
        "remember this",
        "don't forget",
        "dont forget",
        "save this",
        "keep this in mind",
        "you should know",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def normalize(text):
    text = text or ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def word_count(text):
    return len(re.findall(r"\b\w+\b", text or ""))


def parse_timestamp(value):
    if not value:
        return None

    value = value.strip()

    # Remove Unicode narrow no-break spaces
    value = value.replace("\u202f", " ")

    formats = [
        "%b %d, %Y, %I:%M:%S %p %Z",
        "%b %d, %Y, %I:%M %p %Z",
        "%b %d, %Y, %I:%M:%S %p",
        "%b %d, %Y, %I:%M %p",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    return None


def classify_text(text):
    text = normalize(text)

    matches = []

    for category, subcategories in TAXONOMY.items():
        for subcategory, keywords in subcategories.items():
            for keyword in keywords:
                if keyword in text:
                    matches.append((category, subcategory))
                    break

    return matches


def detect_learning_signals(user_text):
    text = normalize(user_text)

    signals = []

    for signal, patterns in LEARNING_SIGNALS.items():
        for pattern in patterns:
            if pattern in text:
                signals.append(signal)
                break

    return signals


def top_words(records, n=30):
    stopwords = {
        "the", "and", "for", "that", "this", "with", "what",
        "how", "why", "you", "your", "are", "was", "were",
        "have", "has", "had", "can", "could", "would", "should",
        "from", "into", "about", "which", "where", "when",
        "then", "than", "just", "like", "want", "please",
        "give", "tell", "need", "does", "did", "will", "its",
        "it's", "they", "them", "their", "there", "here",
        "also", "some", "more", "only", "very", "much",
        "not", "but", "all", "any", "one", "get", "got",
        "make", "use", "using", "know", "think", "really",
    }

    words = Counter()

    for record in records:
        text = normalize(record.get("user", ""))
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]{2,}\b", text)

        for token in tokens:
            if token not in stopwords:
                words[token] += 1

    return words.most_common(n)


# ============================================================
# MAIN
# ============================================================

def main():

    records = []

    with INPUT.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print("\n" + "=" * 70)
    print("RAYA DATASET PROFILE v0.2")
    print("=" * 70)

    total = len(records)

    print(f"\nTotal conversations : {total:,}")

    # --------------------------------------------------------
    # DATA QUALITY
    # --------------------------------------------------------

    empty_user = 0
    empty_assistant = 0

    for r in records:
        if not r.get("user", "").strip():
            empty_user += 1

        if not r.get("assistant", "").strip():
            empty_assistant += 1

    print("\n--- DATA QUALITY ---")
    print(f"Empty user messages     : {empty_user:,}")
    print(f"Empty assistant replies : {empty_assistant:,}")

    # --------------------------------------------------------
    # LENGTH
    # --------------------------------------------------------

    user_lengths = [
        word_count(r.get("user", ""))
        for r in records
    ]

    assistant_lengths = [
        word_count(r.get("assistant", ""))
        for r in records
    ]

    print("\n--- MESSAGE LENGTH ---")

    print(
        f"User      avg={mean(user_lengths):.1f} "
        f"median={median(user_lengths):.1f} "
        f"max={max(user_lengths):,}"
    )

    print(
        f"Assistant avg={mean(assistant_lengths):.1f} "
        f"median={median(assistant_lengths):.1f} "
        f"max={max(assistant_lengths):,}"
    )

    print(f"\nUser <= 5 words   : {sum(x <= 5 for x in user_lengths):,}")
    print(f"User >= 100 words : {sum(x >= 100 for x in user_lengths):,}")
    print(f"User >= 500 words : {sum(x >= 500 for x in user_lengths):,}")
    print(f"User >= 1000 words: {sum(x >= 1000 for x in user_lengths):,}")

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    user_messages = [
        normalize(r.get("user", ""))
        for r in records
        if r.get("user")
    ]

    duplicate_counts = Counter(user_messages)

    duplicate_messages = sum(
        count - 1
        for count in duplicate_counts.values()
        if count > 1
    )

    unique_duplicate_groups = sum(
        1
        for count in duplicate_counts.values()
        if count > 1
    )

    print("\n--- DUPLICATES ---")
    print(f"Duplicate messages : {duplicate_messages:,}")
    print(f"Duplicate groups   : {unique_duplicate_groups:,}")

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    parsed_dates = []
    invalid_timestamps = []

    for r in records:
        timestamp = r.get("timestamp", "")
        parsed = parse_timestamp(timestamp)

        if parsed:
            parsed_dates.append(parsed)
        elif timestamp:
            invalid_timestamps.append(timestamp)

    print("\n--- TIMESTAMPS ---")

    print(f"Parsed timestamps  : {len(parsed_dates):,}")
    print(f"Invalid timestamps : {len(invalid_timestamps):,}")

    if parsed_dates:
        print(f"Earliest           : {min(parsed_dates)}")
        print(f"Latest             : {max(parsed_dates)}")

        year_counts = Counter(x.year for x in parsed_dates)

        print("\nConversations by year:")

        for year, count in sorted(year_counts.items()):
            print(f"  {year}: {count:,}")

    if invalid_timestamps:
        print("\nInvalid timestamp examples:")

        for value in Counter(invalid_timestamps).most_common(10):
            print(f"  {value[0]!r} -> {value[1]}")

    # --------------------------------------------------------
    # TOPICS
    # --------------------------------------------------------

    category_counts = Counter()
    subcategory_counts = Counter()

    record_categories = defaultdict(list)
    record_signals = defaultdict(list)

    for index, record in enumerate(records):

        text = (
            record.get("user", "") +
            "\n" +
            record.get("assistant", "")
        )

        matches = classify_text(text)

        categories = set()
        subcategories = set()

        for category, subcategory in matches:
            categories.add(category)
            subcategories.add(f"{category}/{subcategory}")

        for category in categories:
            category_counts[category] += 1
            record_categories[category].append(index)

        for subcategory in subcategories:
            subcategory_counts[subcategory] += 1

        signals = detect_learning_signals(record.get("user", ""))

        for signal in signals:
            record_signals[signal].append(index)

    print("\n--- BROAD TOPICS ---")

    for category, count in category_counts.most_common():
        percentage = count / total * 100
        print(f"{category:25} {count:5,} ({percentage:5.1f}%)")

    print("\n--- SUBCATEGORIES ---")

    for subcategory, count in subcategory_counts.most_common(40):
        percentage = count / total * 100
        print(f"{subcategory:35} {count:5,} ({percentage:5.1f}%)")

    # --------------------------------------------------------
    # LEARNING SIGNALS
    # --------------------------------------------------------

    print("\n--- LEARNING SIGNALS ---")

    for signal, indexes in sorted(
        record_signals.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    ):
        percentage = len(indexes) / total * 100
        print(f"{signal:20} {len(indexes):5,} ({percentage:5.1f}%)")

    # --------------------------------------------------------
    # TOP USER WORDS
    # --------------------------------------------------------

    print("\n--- TOP USER WORDS ---")

    for word, count in top_words(records):
        print(f"{word:25} {count:,}")

    # --------------------------------------------------------
    # CATEGORY SAMPLES
    # --------------------------------------------------------

    print("\n--- CATEGORY SAMPLES ---")

    for category in category_counts.most_common():

        category_name = category[0]
        indexes = record_categories[category_name]

        print(f"\n### {category_name.upper()}")

        for index in indexes[:3]:
            record = records[index]

            user = record.get("user", "").replace("\n", " ")

            print(f"- {user[:300]}")

    # --------------------------------------------------------
    # LEARNING SIGNAL SAMPLES
    # --------------------------------------------------------

    print("\n--- LEARNING SIGNAL SAMPLES ---")

    for signal, indexes in sorted(
        record_signals.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    ):

        print(f"\n### {signal.upper()}")

        for index in indexes[:5]:

            record = records[index]

            user = record.get("user", "").replace("\n", " ")

            print(f"- {user[:400]}")

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("PROFILE COMPLETE")
    print("=" * 70)

    print("\nImportant:")
    print("Topic classification is heuristic.")
    print("It is NOT yet the final RAYA training classification.")
    print("\nNext step: review the profile before building the classifier.")


if __name__ == "__main__":
    main()