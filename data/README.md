# Data directory

Place local exports here. These paths are gitignored and are not pushed to GitHub.

- `raw/gemini/MyActivity.html` — Gemini activity export → `python3 scripts/parse_gemini.py`
- `raw/chatgpt/*.zip` or `conversations.json` — ChatGPT export → `python3 scripts/parse_chatgpt.py`
- `processed/*.jsonl` — pipeline outputs from `scripts/`

Run the pipeline locally after cloning; see the root README.
