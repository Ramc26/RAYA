#!/usr/bin/env python3
"""
RAYA semantic conversation classifier.

Uses a small local MLX model to decide whether a conversation contains
something RAYA should learn about the user.

Default:
    input  = data/processed/gemini_candidates.jsonl
    output = data/processed/gemini_semantic.jsonl

Run a small validation:
    python3 scripts/semantic_classify.py --limit 20

Run the full candidate set after validation:
    python3 scripts/semantic_classify.py
"""

import argparse
import json
import re
from pathlib import Path

DEFAULT_MODEL = "mlx-community/SmolLM2-360M-Instruct"
DEFAULT_INPUT = "data/processed/gemini_candidates.jsonl"
DEFAULT_OUTPUT = "data/processed/gemini_semantic.jsonl"

# Keep the prompt comfortably below SmolLM2's 2048-token context.
MAX_PROMPT_TOKENS = 1150
MAX_OUTPUT_TOKENS = 120
LOG_EVERY = 10
MAX_RETRIES = 1

SYSTEM_PROMPT = """You classify personal AI conversations for RAYA.

Decide ONLY whether the USER message contains something RAYA should learn
about the user.

Useful:
- preference
- personality explicitly stated by user
- goal
- decision pattern
- memory/fact about user
- communication style
- correction
- useful example of desired assistant behavior

Not useful:
- ordinary coding/debugging
- server logs
- generic research
- facts about companies/technology
- generated content
- questions with no information about the user

Be conservative. Do not infer sensitive traits.

Return ONLY this JSON:
{"value":"high|medium|low|none","signals":[],"learn":true,"reason":"short"}

Allowed signals:
preference, personality, decision_pattern, memory,
communication_style, goal, correction, conversation_example
"""

RETRY_PROMPT = """Your previous response was invalid.

Return ONLY one JSON object.
Do not explain anything.
Do not answer the user's original question.

Exact format:
{"value":"high","signals":[],"learn":true,"reason":"short"}

Use value: high, medium, low, or none.
Use only allowed signals:
preference, personality, decision_pattern, memory,
communication_style, goal, correction, conversation_example
"""


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def truncate_tokens(tokenizer, text, max_tokens):
    text = clean_text(text)
    tokens = tokenizer.encode(text, add_special_tokens=False)

    if len(tokens) <= max_tokens:
        return text

    return tokenizer.decode(
        tokens[:max_tokens],
        skip_special_tokens=True,
    )


def token_count(tokenizer, text):
    return len(tokenizer.encode(text, add_special_tokens=False))


def build_user_prompt(tokenizer, record, compact=False):
    """
    Prioritize the user's own words.

    The assistant response is intentionally tiny because the classifier
    is deciding what RAYA should learn about the USER, not solving the task.
    """
    if compact:
        user_budget = 650
        assistant_budget = 80
    else:
        user_budget = 800
        assistant_budget = 120

    user = truncate_tokens(
        tokenizer,
        record.get("user", ""),
        user_budget,
    )

    assistant = truncate_tokens(
        tokenizer,
        record.get("assistant", ""),
        assistant_budget,
    )

    return (
        "USER:\n"
        f"{user}\n\n"
        "ASSISTANT CONTEXT:\n"
        f"{assistant}\n\n"
        "Classify the USER. Return only JSON."
    )


def make_prompt(tokenizer, record, compact=False, retry=False):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                tokenizer,
                record,
                compact=compact,
            ),
        },
    ]

    if retry:
        messages.append(
            {"role": "user", "content": RETRY_PROMPT}
        )

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    return prompt


def extract_json(text):
    """
    Parse a JSON object even if the model accidentally wraps it in prose.
    """
    text = (text or "").strip()

    text = re.sub(
        r"```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = text.replace("```", "").strip()

    # First try the complete output.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    # Otherwise find the first balanced JSON object.
    start = text.find("{")
    if start == -1:
        raise ValueError(
            f"No JSON object in model output: {text[:300]!r}"
        )

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):
        char = text[i]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1

            if depth == 0:
                candidate = text[start:i + 1]
                return json.loads(candidate)

    raise ValueError(
        f"Unterminated JSON object in model output: {text[:300]!r}"
    )


ALLOWED_VALUES = {"high", "medium", "low", "none"}

ALLOWED_SIGNALS = {
    "preference",
    "personality",
    "decision_pattern",
    "memory",
    "communication_style",
    "goal",
    "correction",
    "conversation_example",
}


def validate(annotation):
    if not isinstance(annotation, dict):
        raise ValueError("Classification is not a JSON object")

    value = annotation.get("value", "none")
    if value not in ALLOWED_VALUES:
        value = "none"

    signals = annotation.get("signals", [])
    if not isinstance(signals, list):
        signals = []

    signals = [
        signal
        for signal in signals
        if signal in ALLOWED_SIGNALS
    ]

    learn = annotation.get("learn", False)
    if not isinstance(learn, bool):
        learn = False

    reason = annotation.get("reason", "")
    if not isinstance(reason, str):
        reason = str(reason)

    # Conservative consistency rules.
    if value == "none":
        learn = False

    return {
        "learning_value": value,
        "signals": signals,
        "raya_should_learn": learn,
        "reason": reason[:300],
    }


def classify_one(model, tokenizer, sampler, record):
    from mlx_lm import generate

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        compact = attempt > 0
        retry = attempt > 0

        prompt = make_prompt(
            tokenizer,
            record,
            compact=compact,
            retry=retry,
        )

        tokens = token_count(tokenizer, prompt)

        if tokens > MAX_PROMPT_TOKENS:
            # One final compact fallback.
            prompt = make_prompt(
                tokenizer,
                record,
                compact=True,
                retry=True,
            )
            tokens = token_count(tokenizer, prompt)

        if tokens > MAX_PROMPT_TOKENS:
            raise ValueError(
                f"Prompt too long after truncation: {tokens} tokens"
            )

        try:
            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=MAX_OUTPUT_TOKENS,
                sampler=sampler,
                verbose=False,
            )

            annotation = extract_json(response)
            return validate(annotation), attempt + 1

        except Exception as exc:
            last_error = exc

    raise last_error


def classify_records(input_path, output_path, model_name, limit=None):
    try:
        from mlx_lm import load
        from mlx_lm.sample_utils import make_sampler
    except ImportError:
        raise SystemExit(
            "mlx-lm is not installed. Run:\n"
            "uv pip install mlx-lm"
        )

    records = []

    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if limit is not None:
        records = records[:limit]

    print(f"Loading model: {model_name}")

    model, tokenizer = load(model_name)
    sampler = make_sampler(temp=0.0)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    success = 0
    failures = 0
    retries = 0

    value_counts = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "none": 0,
    }

    with output_path.open("w", encoding="utf-8") as out:
        for index, record in enumerate(records, 1):
            try:
                annotation, attempts = classify_one(
                    model,
                    tokenizer,
                    sampler,
                    record,
                )

                if attempts > 1:
                    retries += 1

                result = dict(record)
                result["semantic_classification"] = annotation

                out.write(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                success += 1
                value_counts[
                    annotation["learning_value"]
                ] += 1

            except Exception as exc:
                failures += 1

                result = dict(record)
                result["semantic_classification"] = {
                    "learning_value": "none",
                    "signals": [],
                    "raya_should_learn": False,
                    "reason": (
                        f"classification_error: "
                        f"{type(exc).__name__}: "
                        f"{str(exc)[:180]}"
                    ),
                }

                out.write(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                print(
                    f"[ERROR {index}] "
                    f"{type(exc).__name__}: "
                    f"{str(exc)[:220]}"
                )

            if (
                index % LOG_EVERY == 0
                or index == len(records)
            ):
                print(
                    f"[{index:>5}/{len(records):<5}] "
                    f"success={success} "
                    f"failures={failures} "
                    f"retries={retries} "
                    f"| high={value_counts['high']} "
                    f"medium={value_counts['medium']} "
                    f"low={value_counts['low']} "
                    f"none={value_counts['none']}"
                )

    print("\nSemantic classification complete")
    print(f"Input:      {input_path}")
    print(f"Output:     {output_path}")
    print(f"Processed:  {len(records)}")
    print(f"Successful: {success}")
    print(f"Failures:   {failures}")
    print(f"Retries:    {retries}")
    print(
        "Learning values: "
        f"high={value_counts['high']}, "
        f"medium={value_counts['medium']}, "
        f"low={value_counts['low']}, "
        f"none={value_counts['none']}"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    classify_records(
        Path(args.input),
        Path(args.output),
        args.model,
        args.limit,
    )


if __name__ == "__main__":
    main()
