## Mohid Faisal - BSCS23092

# StudySync Resilience Demo

This repository contains a complete submission package for the PDC assignment on resilient distributed systems. The written report analyzes all three failure modes from the prompt, and the code implementation fixes the synchronization bug with optimistic locking in a minimal FastAPI mock of the StudySync backend.


## What Is Implemented

- Part 1: Root-cause analysis for synchronization, webhook coordination, and LLM fault tolerance in `report/report.pdf`
- Part 2: Architecture improvements for all three problems, including a UML-style sequence diagram embedded in the LaTeX report
- Part 3: Working FastAPI implementation of the synchronization fix using optimistic locking
- Part 3 Demo Support: A reproducible script and pytest suite that show the naive lost-update failure and the corrected behavior
- Submission Rule: Global FastAPI middleware that adds `X-Student-ID: BSCS23092` to every API response

## Project Structure

- `app/main.py`: FastAPI application and API routes
- `app/database.py`: SQLite-backed document store with naive and optimistic update paths
- `tests/test_sync.py`: Automated proof that the naive implementation loses updates and the fixed implementation rejects stale writes
- `scripts/demo_sync.py`: Small console demo for a screen-recorded before/after walkthrough
- `report/report.pdf`: PDF report

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
python -m pytest -q
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

## Demo Runbook

This is the exact flow used for the screen recording and live verification.

### Step 0: Show Automated Tests Passing

**Command**

```bat
python -m pytest -q
```

**Purpose**

This verifies that the implementation has working automated test coverage for:

- the custom student header
- the naive lost-update failure case
- the optimistic-locking fix

**Expected Output**

```text
3 passed
```

**What It Signifies**

This confirms the code is behaving correctly before the live demo starts.

### Step 1: Show The FastAPI Server Running

**Terminal 1 Command**

```bat
python -m uvicorn app.main:app --reload
```

**Purpose**

This starts the StudySync FastAPI backend locally.

**Expected Output**

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete
```

**What It Signifies**

This confirms the API server is live and ready to receive requests.

## Live API Demo

### Step 2: Show The Required Custom Header

**Terminal 2 Command**

```bat
curl -i http://127.0.0.1:8000/health
```

**Purpose**

This checks whether every API response includes the required custom middleware header.

**Expected Output**

```text
HTTP/1.1 200 OK
x-student-id: BSCS23092
{"status":"ok"}
```

**What It Signifies**

This satisfies the strict assignment rule requiring `X-Student-ID: BSCS23092` on every API response.

### Step 3: Reset The Demo State

**Command**

```bat
curl -i -X POST http://127.0.0.1:8000/api/admin/reset
```

**Purpose**

This resets the database to a known clean state with one shared document.

**Expected Output**

```text
HTTP/1.1 200 OK
x-student-id: BSCS23092
"content":"Initial shared draft"
"version":1
```

**What It Signifies**

This gives both users the same starting version of the same shared document.

### Step 4: Check The Initial Document

**Command**

```bat
curl -i http://127.0.0.1:8000/api/documents/1
```

**Purpose**

This shows the original state of the shared document before any edits are made.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Initial shared draft"
"version":1
```

**What It Signifies**

This confirms the document starts at version 1 and is ready for the concurrency demo.

## Before Fix: Naive Overwrite

### Step 5: First Naive Write

**Command**

```bat
curl -i -X PUT http://127.0.0.1:8000/api/documents/1/naive ^
  -H "Content-Type: application/json" ^
  -d "{\"content\":\"Alice adds a concurrency-safe summary.\",\"editor\":\"alice\",\"expected_version\":1}"
```

**Purpose**

This simulates User A saving changes to the shared document.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Alice adds a concurrency-safe summary."
"version":2
"last_editor":"alice"
```

**What It Signifies**

Alice's write succeeds and increments the document version from 1 to 2.

### Step 6: Second Stale Naive Write

**Command**

```bat
curl -i -X PUT http://127.0.0.1:8000/api/documents/1/naive ^
  -H "Content-Type: application/json" ^
  -d "{\"content\":\"Bob overwrites the same paragraph with stale data.\",\"editor\":\"bob\",\"expected_version\":1}"
```

**Purpose**

This simulates User B saving an outdated copy based on the old version 1 state.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Bob overwrites the same paragraph with stale data."
"version":3
"last_editor":"bob"
```

**What It Signifies**

This is the bug. Even though Bob used stale data, the naive endpoint still accepts the write.

### Step 7: Show Final State After Naive Bug

**Command**

```bat
curl -i http://127.0.0.1:8000/api/documents/1
```

**Purpose**

This fetches the document after both naive writes have completed.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Bob overwrites the same paragraph with stale data."
"version":3
```

**What It Signifies**

This proves the Lost Update anomaly:

- Alice's update was accepted
- Bob's stale update was also accepted
- Alice's work was silently overwritten

## After Fix: Optimistic Locking

### Step 8: Reset Again

**Command**

```bat
curl -i -X POST http://127.0.0.1:8000/api/admin/reset
```

**Purpose**

This resets the document so the fixed version can be demonstrated from the same clean starting point.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Initial shared draft"
"version":1
```

**What It Signifies**

The document is reset to the original state before testing the fix.

### Step 9: First Safe Optimistic Write

**Command**

```bat
curl -i -X PUT http://127.0.0.1:8000/api/documents/1/optimistic ^
  -H "Content-Type: application/json" ^
  -d "{\"content\":\"Alice adds a concurrency-safe summary.\",\"editor\":\"alice\",\"expected_version\":1}"
```

**Purpose**

This simulates User A saving changes through the fixed optimistic-locking endpoint.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Alice adds a concurrency-safe summary."
"version":2
"last_editor":"alice"
```

**What It Signifies**

Alice's write succeeds because the current version still matches `expected_version = 1`.

### Step 10: Second Stale Optimistic Write

**Command**

```bat
curl -i -X PUT http://127.0.0.1:8000/api/documents/1/optimistic ^
  -H "Content-Type: application/json" ^
  -d "{\"content\":\"Bob tries to save his stale copy.\",\"editor\":\"bob\",\"expected_version\":1}"
```

**Purpose**

This simulates User B trying to save an outdated copy after Alice has already changed the document.

**Expected Output**

```text
HTTP/1.1 409 Conflict
x-student-id: BSCS23092
"message":"Version conflict detected. Refresh and merge before retrying."
"current_document":{"content":"Alice adds a concurrency-safe summary.","version":2}
```

**What It Signifies**

This proves the fix works:

- Bob's stale write is rejected
- the system detects the version mismatch
- the latest server copy is returned for refresh/merge

### Step 11: Show Final Protected State

**Command**

```bat
curl -i http://127.0.0.1:8000/api/documents/1
```

**Purpose**

This verifies the final state of the document after the optimistic-locking conflict.

**Expected Output**

```text
HTTP/1.1 200 OK
"content":"Alice adds a concurrency-safe summary."
"version":2
```

**What It Signifies**

This confirms the final document is correct and Alice's update was preserved.

## Key Technicality

### Naive Endpoint

- Accepts both writes
- Causes silent overwrite
- Demonstrates the Lost Update anomaly

### Optimistic-Locking Endpoint

- Checks `expected_version`
- Rejects stale writes with `409 Conflict`
- Preserves consistency and prevents silent data loss
