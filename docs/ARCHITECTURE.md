# RAYA Architecture

## 1. Overview

RAYA is a personal AI system composed of four main layers:

```text
                    RAYA
                      |
       +--------------+--------------+
       |              |              |
      Model         Memory          Tools
       |              |              |
  Personality     Personal facts   Calendar
  Behavior        History          Web
  Reasoning       Preferences      Files
  Communication   Projects         APIs
       |              |              |
       +--------------+--------------+
                      |
                      v
                Personal Context
                      |
                      v
                   Response
```

---

## 2. Model Layer

Initial model:

**SmolLM2-360M-Instruct**

Fine-tuning:

- Hugging Face Transformers
- TRL
- PEFT / LoRA

The base model remains unchanged.

Personal behavior is learned through LoRA adapters.

```text
Base Model
    +
RAYA LoRA
    =
RAYA Model
```

Future models can replace the 360M model without changing the rest of
the architecture.

---

## 3. Data Layer

```text
Raw Sources
    |
    v
Extraction
    |
    v
Normalized Data
    |
    v
Classification
    |
    +--> Memory
    +--> Training Candidate
    +--> Rejected
```

Raw data is never modified.

---

## 4. Memory Layer

Memory stores information that can change over time.

Examples:

- Current projects
- Current preferences
- Personal facts
- Past events
- Current state

Initial implementation may use SQLite.

Vector search can be added later if required.

---

## 5. Tool Layer

Future tools may include:

- Web search
- Calendar
- Files
- Email
- APIs
- Automation

Tools are separate from the model.

---

## 6. Learning Loop

```text
Conversation
    |
    v
Extract useful information
    |
    v
Human review
    |
    v
Dataset update
    |
    v
LoRA training
    |
    v
Evaluation
    |
    v
New RAYA version
```

Continuous learning will only be automated after the pipeline is proven
stable.
