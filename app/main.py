from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from app.config import DEFAULT_DB_PATH, STUDENT_ID
from app.database import DocumentRecord, DocumentStore
from app.schemas import (
    ConflictResponse,
    DocumentCreateRequest,
    DocumentResponse,
    DocumentUpdateRequest,
    ResetResponse,
)


def create_app(database_path: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="StudySync Resilience Demo",
        description=(
            "Minimal FastAPI mock used to demonstrate a lost-update failure "
            "and an optimistic-locking fix."
        ),
        version="1.0.0",
    )
    app.state.store = DocumentStore(database_path or DEFAULT_DB_PATH)

    @app.middleware("http")
    async def add_student_id_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Student-ID"] = STUDENT_ID
        return response

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": "StudySync Resilience Demo",
            "focus": "Synchronization fix with optimistic locking",
        }

    @app.get("/health")
    def health(request: Request) -> dict[str, str]:
        request.app.state.store.create_schema()
        return {"status": "ok"}

    @app.post("/api/admin/reset", response_model=ResetResponse)
    def reset_demo_state(request: Request) -> ResetResponse:
        document = request.app.state.store.reset_with_seed()
        return ResetResponse(
            message="Database reset with one shared demo document.",
            document=_to_response(document),
        )

    @app.get("/api/admin/state")
    def debug_state(request: Request) -> dict[str, object]:
        return request.app.state.store.diagnostic_state()

    @app.post("/api/documents", response_model=DocumentResponse, status_code=201)
    def create_document(request: Request, payload: DocumentCreateRequest) -> DocumentResponse:
        document = request.app.state.store.create_document(
            title=payload.title,
            content=payload.content,
            editor=payload.editor,
        )
        return _to_response(document)

    @app.get("/api/documents/{document_id}", response_model=DocumentResponse)
    def get_document(request: Request, document_id: int) -> DocumentResponse:
        document = request.app.state.store.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return _to_response(document)

    @app.put("/api/documents/{document_id}/naive", response_model=DocumentResponse)
    def naive_update_document(
        request: Request,
        document_id: int,
        payload: DocumentUpdateRequest,
    ) -> DocumentResponse:
        document = request.app.state.store.naive_update(
            document_id=document_id,
            content=payload.content,
            editor=payload.editor,
        )
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        return _to_response(document)

    @app.put(
        "/api/documents/{document_id}/optimistic",
        response_model=DocumentResponse,
        responses={409: {"model": ConflictResponse}},
    )
    def optimistic_update_document(
        request: Request,
        document_id: int,
        payload: DocumentUpdateRequest,
    ) -> DocumentResponse:
        if payload.expected_version is None:
            raise HTTPException(
                status_code=422,
                detail="expected_version is required for optimistic locking.",
            )
        document, current_document = request.app.state.store.optimistic_update(
            document_id=document_id,
            expected_version=payload.expected_version,
            content=payload.content,
            editor=payload.editor,
        )
        if document is not None:
            return _to_response(document)
        if current_document is None:
            raise HTTPException(status_code=404, detail="Document not found.")
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Version conflict detected. Refresh and merge before retrying.",
                "current_document": _to_response(current_document).model_dump(),
            },
        )

    return app


def _to_response(document: DocumentRecord) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        version=document.version,
        last_editor=document.last_editor,
        updated_at=document.updated_at,
    )


app = create_app()
