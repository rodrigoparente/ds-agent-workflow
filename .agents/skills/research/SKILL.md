---
name: research
description: Interview the user, research via web search (`quick`) or web plus Semantic Scholar and arXiv (`deep`), and write a cited storyline brief to docs/research/<name>.md. Use when the user wants to understand or learn a topic in depth, not for simple lookups.
---

# Research

Produce a brief the user reads to **understand** a subject. Standalone by default; may optionally be linked from a spec later (`Research: docs/research/<name>.md`).

Two modes (the user chooses):

| Mode | Sources | Speed |
|---|---|---|
| `quick` | Web search + reading pages | Minutes |
| `deep` | Web + academic papers (arXiv, Semantic Scholar) | Takes longer; fuller storyline |

Output language: English by default (or match the user's requested language).

## 1. Interview (adaptive)

The user often doesn't know what they want, or doesn't know the terms. Do not research until the goal is clear.

- Use your structured question tool with selectable options (1-3 questions per round; keep going until the goal is clear).
- Find out, in this order, skipping whatever the user already said:
  1. **Topic:** what do they want to understand, and what triggered it?
  2. **Purpose:** what will they do with it (learn, decide, build, write, teach)?
  3. **Current knowledge:** what do they already know? Ask only if they haven't said.
  4. **Focus:** specific angles or terms. Whenever the user is unsure, run a quick landscape search *first* and turn the real subtopics you find into concrete selectable options instead of asking generic questions.
  5. **Mode:** `quick` or `deep`.
- Never invent the goal or the question. If something is missing, ask or offer options.
- **Scope handoff:**
  - **`quick`:** Restate the understanding (topic, focus, and proposed `docs/research/<suggested-name>.md`) in 2-3 lines and start researching immediately (no approval gate).
  - **`deep`:** Share a 3-4 line scope recap (core questions to answer, subtopics, and proposed `docs/research/<suggested-name>.md`, inviting a rename if desired) and **STOP for a quick user confirmation** before launching the 20+ source deep dive.

## 2. Research

Rules for both modes:
- **Read pages, not snippets.** Fetch and read primary sources (papers, official docs, original posts) rather than summaries.
- Cross-check important claims across sources and run independent searches in parallel.
- Number sources (`[1]`, `[2]`, ...) as you go and search for the *foundations* the user will need, not only the specific question.

**quick**: ~6-12 good sources from web search. Enough to build an accurate, well-structured picture.

**deep**: everything in quick, plus papers. Use the helper:

```bash
python3 .agents/skills/research/scripts/papers.py search "query" --limit 10            # Semantic Scholar (citation counts)
python3 .agents/skills/research/scripts/papers.py search "query" --source arxiv        # arXiv (newest/preprints)
```

- Start with survey papers for orientation, then specific papers, then the most-cited foundational ones.
- Read abstracts to triage; read full text via `https://arxiv.org/html/<id>` when available (falling back to `/abs/<id>`).
- Aim for 20+ sources across web and papers.

## 3. Write `docs/research/<name>.md`

Create `docs/research/` if it doesn't exist. Read `references/storyline.md` and follow its structure, uncertainty/citation rules, and word-count targets.

## 4. Stop

Tell the user the file path and give a 2-3 line summary of what's inside. Do not start a spec, experiment, or anything else. The user decides what comes next.
