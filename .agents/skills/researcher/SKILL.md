---
name: researcher
description: Research a topic, algorithm, technique, or dataset across academic papers (arXiv), industry engineering blogs, and open-source benchmarks. Triggers whenever the user wants to know more about X, explore the landscape, compare algorithms, find toy or benchmark datasets, understand state-of-the-art approaches, or conduct literature research before starting an experiment.
---

# Researcher

Researches external literature, industry benchmarks, and open-source implementations to provide an objective technical briefing.

The output is always written to `docs/research/<topic>.md`.

## Process

1. **Scope, clarify, and interact (Use Dialog Box):**
   Understand the user's intent. If the inquiry is broad or open-ended, present 2–3 specific research angles or key constraints (e.g. latency vs. accuracy, CPU scale vs. distributed) via the **dialog box (`ask_question` tool)** so the user can easily select an angle or provide custom instructions via "Other".
2. **Targeted investigation:**
   Perform focused searches across academic literature (arXiv, conference proceedings), engineering blogs, GitHub repositories, and official documentation. Inspect source content directly to verify findings.
3. **Compile technical brief:**
   Write `docs/research/<topic>.md` (at most 2 pages) using the structure below.
4. **Summary & collaborative handoff:**
   Provide a concise 3-line summary in chat with the path to the research file, highlight 1–2 key trade-offs discovered, and wait for the user's direction in chat.

## Brief Structure

```markdown
# <Topic> — Technical Brief

## Overview
Concise explanation of the topic, problem domain, and typical use cases.

## Key Facts & Benchmarks
Relevant dataset sizes, input/output dimensions, standard metrics, and baseline expectations.

## Common Approaches
| Approach | Paradigm (Academic / Industry) | Complexity | Typical Benchmark / Result | Source |
|---|---|---|---|---|
| ... | ... | Low / Med / High | ... | ... |

## Pitfalls & Failure Modes
Data leakage risks, label noise, scalability bottlenecks, and edge cases.

## Key Decisions Ahead
Key architectural choices and evaluation trade-offs for the user to consider.

## Sources
Cited articles, documentation, and repositories reviewed.
```

## Quality Guidelines

- Focus on verifiable facts and source-backed benchmarks.
- Clearly differentiate demonstrated results from theoretical claims.
- Present trade-offs objectively across simplicity, accuracy, and compute requirements.
