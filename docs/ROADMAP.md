# RAYA Roadmap

## Phase 1 — Data Collection

Status: 🟡 In Progress

- [x] Create RAYA project
- [x] Create data structure
- [x] Export Gemini data
- [x] Extract Gemini conversations
- [x] Generate `gemini_raw.jsonl`
- [ ] Export ChatGPT data
- [ ] Extract ChatGPT conversations
- [ ] Normalize all sources

---

## Phase 2 — Data Intelligence

Status: ⬜ Not Started

- [ ] Build data classifier
- [ ] Detect useful conversations
- [ ] Extract personality patterns
- [ ] Extract preferences
- [ ] Extract decision patterns
- [ ] Extract corrections
- [ ] Extract memory candidates
- [ ] Detect duplicates
- [ ] Detect low-value data
- [ ] Human review workflow

---

## Phase 3 — First Dataset

Status: ⬜ Not Started

Initial target:

- ~100 personality examples
- ~100 preference examples
- ~300 conversation examples
- ~100 decision examples
- ~50 correction examples

Quality is more important than the exact number.

---

## Phase 4 — First Model

Status: ⬜ Not Started

- [ ] Download SmolLM2-360M-Instruct
- [ ] Test local inference
- [ ] Prepare training dataset
- [ ] Configure LoRA
- [ ] Train RAYA-360M-v0.1
- [ ] Run evaluation
- [ ] Document results

---

## Phase 5 — Memory

Status: ⬜ Not Started

- [ ] Define memory schema
- [ ] Implement SQLite memory
- [ ] Add memory extraction
- [ ] Add memory retrieval
- [ ] Test memory accuracy

---

## Phase 6 — Personal Assistant

Status: ⬜ Not Started

- [ ] Web search
- [ ] Calendar
- [ ] Files
- [ ] APIs
- [ ] Tool selection
- [ ] Action execution

---

## Phase 7 — Continuous Learning

Status: ⬜ Future

```text
New conversation
      ↓
Data extraction
      ↓
Candidate generation
      ↓
Review
      ↓
Dataset version
      ↓
LoRA training
      ↓
Evaluation
      ↓
Accept / Rollback
```

Automatic daily training will only be enabled after this pipeline is
reliable.

---

## Long-Term

Potential future models:

```text
360M
 ↓
500M–1B
 ↓
3B+
```

The data, memory and evaluation systems should remain independent of the
model size.