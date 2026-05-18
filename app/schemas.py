from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    editor: str = Field(..., min_length=1, max_length=80)


class DocumentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    editor: str = Field(..., min_length=1, max_length=80)
    expected_version: int | None = Field(
        default=None,
        ge=1,
        description="Client-side version used by optimistic locking.",
    )


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    version: int
    last_editor: str
    updated_at: str


class ResetResponse(BaseModel):
    message: str
    document: DocumentResponse


class ConflictResponse(BaseModel):
    detail: str
    current_document: DocumentResponse
