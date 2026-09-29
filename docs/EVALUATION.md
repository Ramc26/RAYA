# RAYA Evaluation

## 1. Purpose

Evaluation determines whether a new RAYA version is actually better than
the previous version.

More training does not automatically mean better performance.

---

## 2. Evaluation Areas

RAYA will initially be evaluated on:

| Area | What we measure |
|---|---|
| Personality | Does it behave consistently? |
| Preferences | Does it follow known preferences? |
| Instruction | Does it follow requests correctly? |
| Decisions | Does it understand decision patterns? |
| Conversation | Is the interaction useful? |
| Memory | Does it use relevant memory? |
| Hallucination | Does it invent personal facts? |
| Format | Does it follow requested formats? |
| Safety | Does it avoid unsafe behavior? |

---

## 3. Evaluation Dataset

The evaluation dataset must be separate from training data.

```text
Training Data
      |
      v
    Train
      |
      v
 RAYA-v0.x
      |
      v
Evaluation Dataset
      |
      v
Evaluation Report
```

Evaluation examples should include:

- Normal questions
- Personal preference questions
- Decision scenarios
- Correction scenarios
- Memory scenarios
- Edge cases

---

## 4. Version Comparison

Each version should record:

```text
Model version
Dataset version
Training configuration
Evaluation results
Known issues
```

Example:

```text
RAYA-360M-v0.2

Personality:       82%
Preferences:       78%
Instructions:      90%
Decision patterns: 71%
Memory:            85%

Known issues:
- Too verbose
- Weak long-term reasoning
```

Numbers are for internal comparison only and should not be treated as a
single overall model score.

---

## 5. Acceptance

A new version should only replace the previous version when:

- Important behaviors improve or remain stable
- No major regressions are introduced
- Memory behavior remains reliable
- The model does not learn incorrect personal information

Previous versions must remain available for rollback.
