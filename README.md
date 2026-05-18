Mohid Faisal - BSCS23092

# StudySync Resilience Demo

This repository contains a complete submission package for the PDC assignment on resilient distributed systems. The written report analyzes all three failure modes from the prompt, and the code implementation fixes the synchronization bug with optimistic locking in a minimal FastAPI mock of the StudySync backend.


## What Is Implemented

- Part 1: Root-cause analysis for synchronization, webhook coordination, and LLM fault tolerance in `report/report.tex`
- Part 2: Architecture improvements for all three problems, including a UML-style sequence diagram embedded in the LaTeX report
- Part 3: Working FastAPI implementation of the synchronization fix using optimistic locking
- Part 3 Demo Support: A reproducible script and pytest suite that show the naive lost-update failure and the corrected behavior
- Submission Rule: Global FastAPI middleware that adds `X-Student-ID: BSCS23092` to every API response

## Project Structure

- `app/main.py`: FastAPI application and API routes
- `app/database.py`: SQLite-backed document store with naive and optimistic update paths
- `tests/test_sync.py`: Automated proof that the naive implementation loses updates and the fixed implementation rejects stale writes
- `scripts/demo_sync.py`: Small console demo for a screen-recorded before/after walkthrough
- `report/report.tex`: LaTeX source for the PDF report

## Setup

Create a virtual environment, install dependencies, and run the app:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000` and the interactive docs at `http://127.0.0.1:8000/docs`.

## Run The Tests

```powershell
pytest
```

## Run The Demo Script

This script is useful for the 2-minute video because it prints the failure case first and the fixed behavior second:

```powershell
python -m scripts.demo_sync
```

## Suggested Demo Flow

1. Start the FastAPI app with `uvicorn app.main:app --reload`.
   You can also use `python -m uvicorn app.main:app --reload` if `uvicorn` is not on your PATH.
2. Open `/docs` and call `POST /api/admin/reset`.
3. Show the `PUT /api/documents/{id}/naive` route being used twice from the same base version so one edit is silently overwritten.
4. Reset again and repeat with `PUT /api/documents/{id}/optimistic`.
5. Highlight the `409 Conflict` response and the preserved final content.
6. Point out the `X-Student-ID` response header in Swagger or browser dev tools.