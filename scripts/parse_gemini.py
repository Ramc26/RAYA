from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import json
import re


INPUT = Path("data/raw/gemini/MyActivity.html")
OUTPUT = Path("data/processed/gemini_raw.jsonl")


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving readable paragraphs."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_entry(entry, index):
    """
    Extract one Gemini activity entry.

    Expected structure:

        Prompted USER MESSAGE
        <br>
        TIMESTAMP
        <br>
        ASSISTANT RESPONSE
    """

    # Find the text node beginning with "Prompted"
    prompt_node = None

    for node in entry.find_all(string=True):
        if node.strip().startswith("Prompted"):
            prompt_node = node
            break

    if prompt_node is None:
        return None

    raw_prompt = prompt_node.strip()

    # Remove "Prompted"
    prompt = re.sub(
        r"^Prompted\s*",
        "",
        raw_prompt,
        count=1
    ).strip()

    # Find direct <br> tags
    brs = entry.find_all("br", recursive=False)

    timestamp = None
    response_html = ""

    if len(brs) >= 2:

        # Text immediately after first <br>
        current = brs[0].next_sibling

        timestamp_parts = []

        while current is not None and current != brs[1]:
            if isinstance(current, NavigableString):
                timestamp_parts.append(str(current))
            current = current.next_sibling

        timestamp = clean_text(" ".join(timestamp_parts))

        # Everything after second <br> is the response
        response_parts = []

        current = brs[1].next_sibling

        while current is not None:
            response_parts.append(str(current))
            current = current.next_sibling

        response_html = "".join(response_parts).strip()

    # Convert response HTML to clean text
    response_soup = BeautifulSoup(response_html, "lxml")

    # Preserve useful structural separation
    for tag in response_soup.find_all(
        ["p", "div", "h1", "h2", "h3", "h4", "li", "tr"]
    ):
        tag.append("\n")

    response_text = clean_text(
        response_soup.get_text(" ", strip=False)
    )

    return {
        "id": f"gemini_{index:06d}",
        "source": "gemini",
        "timestamp": timestamp,
        "user": prompt,
        "assistant": response_text,
        "assistant_html": response_html,
    }


def main():

    print(f"Reading: {INPUT}")

    with INPUT.open("r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    entries = soup.select(
        "div.content-cell.mdl-cell.mdl-cell--6-col"
    )

    print(f"Candidate entries found: {len(entries)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with OUTPUT.open("w", encoding="utf-8") as out:

        for entry in entries:

            record = extract_entry(entry, count + 1)

            if record is None:
                continue

            # Only save actual Prompted entries
            if not record["user"]:
                continue

            out.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

            count += 1

    print()
    print("Done!")
    print(f"Extracted conversations: {count}")
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()