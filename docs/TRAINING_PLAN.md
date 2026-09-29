# RAYA Training Plan

## Objective

Train a small personal language model that learns:

- RAYA's personality
- User communication preferences
- User-specific response patterns
- Decision-making patterns
- Corrections from previous interactions

The model should complement external memory and tools rather than replace them.

---

## Initial Model

The first experiment uses:

**SmolLM2-360M-Instruct**

The initial goal is not to create a powerful general-purpose model.

The goal is to determine whether a small model can learn useful personal behavior.

---

## Training Method

Use:

- Hugging Face Transformers
- PEFT
- LoRA
- TRL where useful

Do not initially perform full model fine-tuning.

Conceptually:

```text
Base Model
    +
Personal Training Data
    ↓
LoRA Adapter
    ↓
RAYA Model
```

The original base model remains unchanged.

---

## Training Data

Training examples will eventually use a conversational format such as:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ]
}
```

The dataset should be generated from reviewed examples rather than directly training on raw exports.

---

## Training Pipeline

```text
Raw Conversations
        ↓
Normalize
        ↓
Classify
        ↓
Human Review
        ↓
Training Dataset
        ↓
Train LoRA
        ↓
Evaluate
        ↓
Accept / Reject
        ↓
Version Model
```

---

## First Training Run

The first run should be deliberately small.

Objectives:

1. Verify the complete training pipeline.
2. Confirm the model can train locally.
3. Confirm LoRA works on Apple Silicon.
4. Measure memory usage.
5. Compare model behavior before and after training.
6. Identify weaknesses in the dataset.

Do not optimize aggressively during the first experiment.

---

## Evaluation

Every trained version should be evaluated against a fixed evaluation set.

Evaluation should measure:

- Correctness
- Relevance
- Personality consistency
- Preference adherence
- Communication style
- Instruction following
- Hallucination
- Regression from previous versions

A model should not be accepted simply because training loss decreases.

---

## Model Versioning

Every accepted model should have a version.

Example:

```text
raya-v0.1
raya-v0.2
raya-v0.3
```

Keep:

- Base model
- LoRA adapter
- Training dataset version
- Evaluation results
- Training configuration

This allows rollback when a new training run makes behavior worse.

---

## Incremental Learning

RAYA should eventually support continuous learning.

However, new conversations should NOT immediately update model weights.

Initial approach:

```text
Conversation
    ↓
Candidate Learning Signal
    ↓
Review
    ↓
Dataset Update
    ↓
Periodic Training
    ↓
Evaluation
    ↓
New Model Version
```

Training frequency can increase only after the pipeline becomes reliable.

---

## Memory vs Training

Not every new fact should trigger training.

Example:

```text
"I bought a new watch."
        ↓
Memory
```

But:

```text
"I always prefer watches with unusual designs."
        ↓
Potential training signal
```

This distinction prevents the model from becoming outdated or overfitted to temporary information.

---

## Long-Term Goal

The long-term RAYA system should combine:

```text
             ┌──────────────┐
             │   RAYA Model │
             └──────┬───────┘
                    │
       ┌────────────┼────────────┐
       ↓            ↓            ↓
    Memory        Tools       Training
       │            │            │
       └────────────┼────────────┘
                    ↓
              Personal AI
```

The model provides behavior.

Memory provides personal context.

Tools provide real-world capabilities.

Training gradually improves the behavior layer.

---

## Core Principle

> Do not train RAYA to remember everything.
> Train RAYA to behave like RAYA.
