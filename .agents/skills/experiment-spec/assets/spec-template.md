# <NN-name>

Status: draft | approved | executed
Builds on: <NN-name> (optional, delete if none)
Research: docs/research/<topic>.md (optional, delete if none)

## Overview
What we are exploring, analyzing, or building. Clear, concise description without requiring artificial goals or metrics.

## Data & Inputs
Source datasets, files, model artifacts, or parameters (consult `data-catalog` if using lake tables).
Clearly document the data management process:
- Sources & join keys: ...
- Deduplication & filters: ...
- Transformations & shared feature logic (`scripts/<domain>_features.py` if reused): ...

## Approach
Steps to take:
1. ...
2. ...

## Deliverable
- Notebook (`notebooks/py/<NN-name>.py` → `notebooks/<NN-name>.ipynb`), script (`scripts/<NN-name>.py`), or app/API (`apps/<NN>_<name>_app.py` / `apps/<NN>_<name>_api.py`).
- Optional model artifact (`models/<NN-name>.joblib`), shared helper (`scripts/<domain>_features.py`), unit tests (`tests/test_<name>.py`), or figure (`docs/figures/<NN-name>_summary.png`).

## Assumptions (confirm)
- Choices or defaults to confirm with the user. (Remove once confirmed).

## Done When
- [ ] Key criteria for completion (or: open-ended exploration / user confirms satisfied).

## Updates (if revisited)
- *[v1 - Initial Spec]:* ...
- *[v2 - Iteration Reason]:* What changed, why, and whether `REFRESH_DATA = True` is required.
