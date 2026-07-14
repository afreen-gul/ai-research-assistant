"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    citation_style: str = "apa"


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    response: str
    tool_events: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    document: dict[str, Any] | None = None


class SessionCreate(BaseModel):
    title: str = "New Research Session"


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    tool_events: list[dict[str, Any]] = []
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentOut(BaseModel):
    id: str
    title: str
    doc_type: str
    content: str
    citations: list[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    title: str = "Untitled Note"
    content: str = ""
    session_id: str | None = None


class NoteOut(BaseModel):
    id: str
    title: str
    content: str
    session_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class SavedPaperCreate(BaseModel):
    title: str
    authors: str = ""
    url: str = ""
    abstract: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class SavedPaperOut(BaseModel):
    id: str
    title: str
    authors: str
    url: str
    abstract: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchHistoryOut(BaseModel):
    id: str
    query: str
    results_count: str
    session_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    content: str
    title: str = "Research Document"
    format: str = "markdown"
    bibliography: list[str] = []
    citation_style: str = "apa"


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    username: str


class PDFUploadResponse(BaseModel):
    file_id: str
    structured: dict[str, Any]
    metadata: dict[str, Any]
    chunks_ingested: int
