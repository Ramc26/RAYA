# RAYA Data Strategy

## Purpose

RAYA should learn from personal data without blindly training on everything.

The goal is to identify useful signals about:

- Personality
- Preferences
- Communication style
- Decision patterns
- Corrections
- Recurring behaviors
- Stable personal facts

Raw data should remain untouched.

---

## Data Flow

```text
Raw Data
   ↓
Parsing
   ↓
Normalization
   ↓
Classification
   ↓
Human Review
   ↓
Training Dataset
   ↓
Evaluation
   ↓
Model Training
```

---

## Raw Data

Raw sources may include:

- ChatGPT exports
- Gemini exports
- Future AI conversations
- Personal notes
- Other explicitly provided data

Raw files are immutable.

Example:

```text
data/raw/
├── chatgpt/
├── gemini/
└── other/
```

---

## Unified Raw Format

Different sources should eventually be converted into one common structure.

```json
{
  "id": "gemini_000001",
  "source": "gemini",
  "timestamp": "...",
  "user": "...",
  "assistant": "..."
}
```

The original source should always remain identifiable.

---

## Personal Dataset Categories

RAYA uses separate datasets for different learning signals.

### 1. Personality

Stable behavioral characteristics.

Examples:

- Communication style
- Humor
- Directness
- Reasoning style
- Things the user consistently values

### 2. Preferences

Things the user likes, dislikes, or prefers.

Examples:

- Food preferences
- Technology preferences
- Writing preferences
- Shopping preferences

### 3. Conversations

Useful examples of how RAYA should respond in different situations.

### 4. Decisions

Examples showing how the user evaluates options and makes decisions.

### 5. Corrections

High-value examples where the user corrects RAYA.

Examples:

- "That's not what I meant."
- "Keep it shorter."
- "Don't explain this much."
- "I prefer X over Y."

Corrections are especially useful for improving behavior.

### 6. Memory

Facts that should be remembered but should NOT necessarily become model weights.

Examples:

- Current projects
- Current devices
- Current job
- Temporary plans
- Current purchases

Memory should normally live outside the model.

---

## What Should Become Model Knowledge?

Prefer training the model on:

- Personality
- Communication style
- Stable preferences
- Reasoning patterns
- Response patterns
- Repeated corrections

Prefer external memory for:

- Current facts
- Dates
- Projects
- Temporary preferences
- Lists
- Changing information

---

## Quality Rules

RAYA should prioritize quality over dataset size.

Avoid:

- Duplicate conversations
- Low-information conversations
- Random factual questions
- Sensitive information without a clear reason
- Temporary information as permanent personality
- Training on incorrect assistant responses

---

## Human Review

Initial dataset generation should require human review.

```text
Raw Conversation
      ↓
Candidate
      ↓
Review
   ↙     ↘
Accept   Reject
   ↓
Training Dataset
```

Automation can increase gradually after the pipeline becomes reliable.

---

## Initial Dataset Target

The first training dataset is approximately:

- 100 personality examples
- 100 preference examples
- 300 conversation examples
- 100 decision examples
- 50 correction examples

Approximately **650 high-quality examples**.

These are targets, not requirements.

---

## Core Principle

> Collect first. Understand second. Train third. Automate last.
