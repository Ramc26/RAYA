# RAYA

> A private, continuously improving personal AI built around my personality,
> preferences, knowledge, decision patterns, memories, and workflows.

---

## 1. What is RAYA?

RAYA is a personal AI project designed to gradually become a highly
personalized assistant that understands:

- How I communicate
- How I think and make decisions
- My preferences
- My interests and knowledge
- My recurring workflows
- My personal context
- My corrections and feedback
- My long-term memories

The long-term goal is not simply to build a chatbot that knows facts about me.

The goal is to build an AI system that can:

1. Understand me
2. Communicate in a way that fits me
3. Remember relevant personal context
4. Learn from my feedback
5. Reason according to learned behavioral patterns
6. Use external tools
7. Eventually perform actions on my behalf

---



# 2. Core Philosophy

RAYA will NOT try to store my entire life inside model weights.

Instead, the system separates:

### Model

The model learns:

- Personality
- Communication style
- Behavioral patterns
- Decision-making patterns
- Response preferences
- How to interpret my instructions



### Memory

The memory system stores:

- Current facts
- Personal information
- Projects
- Relationships
- Preferences that may change
- Historical events
- Current state



### Tools

Tools allow RAYA to:

- Search the web
- Access files
- Work with calendars
- Perform external actions
- Interact with APIs
- Execute workflows

Therefore:

```text
                 RAYA
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
    MODEL       MEMORY       TOOLS
       |           |           |
 Personality   Personal     Actions
 Behavior      Context      APIs
 Reasoning     History      Services
```

---



# 3. Initial Model

The first model will be:

**Hugging Face SmolLM2-360M-Instruct**

Target size:

```
~360M parameters
```

The initial goal is not to train a language model from scratch.

The model is already pretrained to understand language.

RAYA will adapt it to my personal behavior using parameter-efficient  
fine-tuning.

Initial approach:

```
SmolLM2-360M-Instruct
        |
        + Personal training data
        |
        v
      LoRA
        |
        v
RAYA-360M-v1
```

---



# 4. Why 360M?

The first goal is experimentation, not maximum intelligence.

The model needs to be:

- Small enough to run locally
- Small enough to fine-tune on Apple Silicon
- Cheap/free to experiment with
- Fast enough for repeated experiments
- Easy to version
- Easy to replace later

The initial hardware target is:

```
Apple Silicon Mac
16 GB unified memory
```

The 360M model is the first experimental model.

The architecture must remain model-agnostic so that a larger model can  
replace it later.

Possible future progression:

```
360M
  ↓
500M / ~1B
  ↓
3B+
```

The datasets and memory system should remain reusable across model sizes.

---



# 5. Training Strategy

RAYA will use **LoRA / Parameter-Efficient Fine-Tuning (PEFT)** initially.

We will NOT repeatedly train the complete base model.

Instead:

```
                Base Model
                    |
                    | frozen
                    v
             +--------------+
             | LoRA Adapter  |
             +--------------+
                    |
                    v
              RAYA Model
```

This allows multiple versions of RAYA to be created without duplicating  
the entire base model.

Example:

```
RAYA-v0.1
RAYA-v0.2
RAYA-v0.3
RAYA-v1.0
```

---



# 6. Personal Data Strategy

Raw personal data will never directly become training data.

The pipeline is:

```
Raw Data
   |
   v
Extraction
   |
   v
Normalization
   |
   v
Classification
   |
   v
Candidate Data
   |
   v
Human Review
   |
   v
Training Dataset
   |
   v
LoRA Fine-Tuning
```

The raw data must always remain untouched.

---



# 7. Raw Data Sources

Initial sources include:

- ChatGPT conversations
- Gemini conversations
- Future AI assistants
- Personal notes
- Documents
- Selected emails
- Other personal knowledge sources

Current Gemini source:

```
data/raw/gemini/MyActivity.html
```

Current extracted Gemini data:

```
data/processed/gemini_raw.jsonl
```

Current extraction result:

```
~5,475 Gemini conversations/interactions
```

ChatGPT export is currently being prepared.

---



# 8. Raw Data Directory

```
data/
|
+-- raw/
|   |
|   +-- gemini/
|   |   +-- MyActivity.html
|   |
|   +-- chatgpt/
|   |   +-- export.zip
|   |
|   +-- claude/
|   |
|   +-- other/
|
+-- processed/
|
+-- training/
|
+-- evaluation/
```

Raw source files must not be modified.

---



# 9. Personal Dataset Categories

The initial training pipeline will create the following datasets:

```
personality.jsonl
preferences.jsonl
conversations.jsonl
decisions.jsonl
corrections.jsonl
```

A separate memory dataset/system will be maintained for facts that should  
not be permanently embedded into model weights.

---



# 10. Personality Dataset

Purpose:

Teach RAYA how I communicate and how I want the assistant to behave.

Examples include:

- Communication style
- Desired response length
- Humor
- Explanation style
- How uncertainty should be handled
- How disagreements should be presented
- How recommendations should be structured
- How technical explanations should be given

Example:

```
{
  "messages": [
    {
      "role": "user",
      "content": "Give me the answer first and then explain why."
    },
    {
      "role": "assistant",
      "content": "Lead with the conclusion, then give the reasoning briefly."
    }
  ]
}
```

---



# 11. Preferences Dataset

Purpose:

Teach stable preferences.

Examples:

- Technology preferences
- Food preferences
- Communication preferences
- Learning preferences
- UI preferences
- Shopping preferences
- Workflow preferences

Temporary facts should NOT automatically become training data.

Example:

```
Current phone
Current salary
Current account balance
Current stock holdings
Current project status
```

These belong in memory.

---



# 12. Conversations Dataset

Purpose:

Teach RAYA from high-quality examples of actual interaction.

Best sources:

- High-quality ChatGPT conversations
- High-quality Gemini conversations
- Conversations where I corrected the AI
- Conversations where the final answer matched my expectations
- Conversations showing how I communicate

We will NOT blindly train on every conversation.

Low-value conversations will be filtered.

Examples of low-value data:

- "What's the weather?"
- One-off factual questions
- Repetitive searches
- Temporary information
- AI mistakes
- Irrelevant conversations

---



# 13. Decisions Dataset

Purpose:

Teach RAYA how I approach decisions.

Useful structure:

```
Situation
    ↓
Options
    ↓
Constraints
    ↓
Reasoning
    ↓
Decision
    ↓
Outcome
```

The goal is to learn decision patterns rather than memorize individual  
decisions.

Example:

```
{
  "situation": "Choosing a local model",
  "options": ["360M", "1B"],
  "constraints": ["16GB Mac", "local training"],
  "reasoning": "Validate the pipeline before increasing compute requirements.",
  "decision": "Start with the smaller model."
}
```

---



# 14. Corrections Dataset

Corrections are considered high-value training data.

Examples:

- "That's not what I meant."
- "Keep it shorter."
- "Don't recommend; compare."
- "You missed this constraint."
- "That's incorrect."
- "Use this format instead."

These examples reveal where the assistant fails to match my expectations.

Therefore:

```
AI mistake
    ↓
My correction
    ↓
Desired behavior
    ↓
Training example
```

---



# 15. Memory vs Training

This distinction is fundamental.

### Training

Stores relatively stable behavioral patterns.

Example:

```
I prefer concise technical explanations.
```



### Memory

Stores changing personal information.

Example:

```
Current phone = ...
Current project = ...
Current investment = ...
Current preference = ...
```

Architecture:

```
                Personal AI
                     |
          +----------+----------+
          |                     |
       Model                  Memory
          |                     |
  Stable behavior         Current facts
  Personality             Personal context
  Preferences             History
  Reasoning patterns      State
```

A memory update should NOT require retraining the model.

---



# 16. Dataset Generation

Training examples will be generated from raw data using a  
semi-automated pipeline.

```
5,000+ Gemini conversations
        +
ChatGPT conversations
        +
Other sources
        |
        v
   Data Miner
        |
        v
Candidate Examples
        |
        v
Classification
        |
        +--> Personality
        +--> Preferences
        +--> Conversations
        +--> Decisions
        +--> Corrections
        +--> Memory
        +--> Rejected
        |
        v
Human Review
        |
        v
Training Dataset
```

The system should never automatically train on unverified personal  
information.

---



# 17. Initial Dataset Target

The first experiment will NOT attempt to create thousands of examples.

Initial target:

```
Personality       ~100
Preferences       ~100
Conversations     ~300
Decisions         ~100
Corrections       ~50
--------------------------------
Initial dataset   ~650 examples
```

These are targets, not hard requirements.

Quality is more important than quantity.

We will start smaller if necessary.

---



# 18. Incremental Learning

RAYA should eventually support continuous improvement.

Conceptually:

```
New Conversations
       |
       v
Data Extraction
       |
       v
Candidate Memories / Training Examples
       |
       v
Review
       |
       v
Dataset Version
       |
       v
LoRA Training
       |
       v
Evaluation
       |
       +---- Better? ---- YES ---> New Version
       |
       +---- Worse? ---- NO ----> Rollback
```

We will NOT blindly retrain every day initially.

Daily/continuous training will only be introduced after the complete  
pipeline is stable.

---



# 19. Model Versioning

Every trained model must have a version.

Example:

```
RAYA-360M-v0.1
RAYA-360M-v0.2
RAYA-360M-v0.3
RAYA-360M-v1.0
```

Each model version must be associated with:

- Dataset version
- Training configuration
- Base model
- LoRA configuration
- Evaluation results
- Creation date
- Known limitations

Example:

```
RAYA-360M-v0.2

Base:
SmolLM2-360M-Instruct

Dataset:
dataset-v0.2

Training:
LoRA

Evaluation:
82/100

Known issues:
- Too verbose
- Weak decision reasoning
```

---



# 20. Evaluation

RAYA must be evaluated before accepting a new model version.

Evaluation categories:

```
Personality consistency
Preference adherence
Instruction following
Decision reasoning
Conversation quality
Memory usage
Hallucination
Safety
Tool usage
Response format
```

We will maintain a fixed evaluation dataset that is NOT used for training.

```
training data
       |
       v
     TRAIN
       |
       v
   RAYA-vX
       |
       v
 evaluation dataset
       |
       v
 comparison
       |
       v
 accept / reject
```

---



# 21. Development Environment

Primary development environment:

```
Mac
Apple Silicon
16 GB unified memory
Cursor
Python
```

Cursor will be the primary environment for:

- Writing Python scripts
- Running scripts
- Debugging
- Dataset processing
- Training experiments
- Evaluation
- Project documentation

---



# 22. Initial Technology Stack



### Model

```
SmolLM2-360M-Instruct
```



### Fine-tuning

```
Hugging Face Transformers
Hugging Face TRL
PEFT / LoRA
```



### Data

```
JSONL
```



### Python

```
Python 3
```



### Memory

Initial experiments may use:

```
SQLite
```

A vector database can be introduced later if needed.

Potential future options:

```
Qdrant
Milvus
FAISS
```

---



# 23. Initial Project Structure

```
RAYA/
|
+-- README.md
|
+-- docs/
|   +-- DATA_STRATEGY.md
|   +-- TRAINING_PLAN.md
|   +-- EVALUATION.md
|
+-- data/
|   |
|   +-- raw/
|   |   +-- gemini/
|   |   +-- chatgpt/
|   |   +-- claude/
|   |   +-- other/
|   |
|   +-- processed/
|   |
|   +-- training/
|   |
|   +-- evaluation/
|
+-- models/
|   +-- base/
|   +-- adapters/
|   +-- releases/
|
+-- scripts/
|   +-- parse_gemini.py
|   +-- parse_chatgpt.py
|   +-- classify_data.py
|   +-- build_dataset.py
|   +-- train.py
|   +-- evaluate.py
|
+-- configs/
|
+-- memory/
|
+-- requirements.txt
|
+-- .gitignore
```

---



# 24. Current Progress



## Completed

- RAYA project initialized
- Raw data directory created
- Gemini Takeout collected
- Gemini `MyActivity.html` identified
- Gemini HTML parser created
- Gemini conversations extracted
- ~5,475 Gemini interactions extracted
- `gemini_raw.jsonl` created



## In Progress

- ChatGPT data export
- ChatGPT parser
- Unified raw-data format
- Data classification
- Memory extraction
- Training candidate generation
- Human review workflow



## Future

- Initial ~650-example dataset
- First LoRA training
- RAYA-360M-v0.1
- Evaluation framework
- RAYA memory system
- Tool integration
- Incremental learning
- Automated model versioning
- Larger model experiments

---



# 25. Current Principle

> **Collect first. Understand second. Train third. Automate last.**

RAYA should never blindly learn from everything I have ever said.

The system should distinguish:

```
What I said
       ≠
What is currently true
       ≠
What I prefer
       ≠
How I behave
       ≠
How I make decisions
       ≠
What the model should learn
```

This separation is fundamental to the RAYA architecture.

---



# 26. Long-Term Vision

The eventual RAYA system should look like:

```
                         RAYA
                          |
        +-----------------+------------------+
        |                 |                  |
        v                 v                  v
     MODEL         TRAINING_PLAN    MEMORY             TOOLS
        |                 |                  |
   Personality       Personal facts      Calendar
   Reasoning         History             Email
   Behavior          Preferences         Web
   Communication     Projects            Files
        |                 |                  |
        +-----------------+------------------+
                          |
                          v
                   Personal Context
                          |
                          v
                    Decision Engine
                          |
                          v
                     Action Layer
```

The ultimate objective is a private personal AI that becomes increasingly  
useful through controlled learning while keeping personal data,  
memory, datasets, and model versions under my control.

---



## Status

**Project:** RAYA  
**Stage:** Data Collection & Extraction  
**Current Model:** SmolLM2-360M-Instruct  
**Training:** Not started  
**Hardware:** Apple Silicon Mac, 16 GB  
**Development:** Cursor  
**Current Raw Source:** Gemini  
**Current Extracted Records:** ~5,475