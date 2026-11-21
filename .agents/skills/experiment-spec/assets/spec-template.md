# <NN-name>

Status: draft | approved | executed
Builds on: <NN-name> (optional, delete if none)
Research: docs/research/<name>.md (optional, delete if none)

## Overview
What we are exploring, analyzing, or building. Clear, concise description without requiring artificial goals or metrics.

## Data & Inputs
Source tables, datasets, files, artifacts, or parameters (consult `data-catalog` if using documented project tables).
Clearly document the data management process:
- Sources & join keys: ...
- Deduplication & filters: ...
- Transformations & preprocessing: ...

## Approach
Steps to take:
1. ...
2. ...

## Deliverable
- Notebook (`notebooks/py/<NN-name>.py` → `notebooks/<NN-name>.ipynb`), script (`scripts/<name>.py`), or application (`apps/<name>.py`).
- Optional artifacts: saved models (`models/`), shared modules (`scripts/`), tests (`tests/`), or figures (`docs/figures/<NN-name>_*.png`).

## Assumptions (confirm)
- Choices or defaults to confirm with the user. (Remove once confirmed).

## Done When
- [ ] Key criteria for completion (or: open-ended exploration / user confirms satisfied).

## Updates (if revisited)
- *[v1 - Initial Spec]:* ...
- *[v2 - Update]:* What changed and why (note `REFRESH_DATA = True` if data inputs changed).
