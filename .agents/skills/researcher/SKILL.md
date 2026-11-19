---
name: researcher
description: Research a topic, algorithm, technique, or dataset across academic papers (arXiv), industry engineering blogs, and open-source benchmarks. Triggers whenever the user wants to know more about X, explore the landscape, compare algorithms, find toy or benchmark datasets, understand state-of-the-art approaches, or conduct literature research before starting an experiment.
---

# Researcher

Researches external literature, industry benchmarks, and open-source implementations into an objective technical brief at `docs/research/<topic>.md`.

## Process

1. **Scope & clarify:**
   If the inquiry is broad or open-ended, propose 2–3 research angles or constraints (e.g., latency vs. accuracy, single-node vs. distributed) via `ask_question`.
2. **Targeted investigation:**
   Search academic literature (arXiv, conference proceedings), engineering blogs, GitHub repositories, and official docs; inspect primary sources directly to verify claims.
3. **Compile brief (`docs/research/<topic>.md`):**
   Write at most 2 pages using the structure below, focusing on verifiable facts, source-backed benchmarks, and objective trade-offs (distinguishing demonstrated results from theoretical claims).
4. **Handoff:**
   Share a 3-line summary in chat with a link to `docs/research/<topic>.md`, highlight 1–2 key trade-offs, and wait for user direction.

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
