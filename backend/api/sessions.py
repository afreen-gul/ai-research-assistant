"""Session, notes, saved papers, and search history endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    DocumentOut,
    MessageOut,
    NoteCreate,
    NoteOut,
    SavedPaperCreate,
    SavedPaperOut,
    SearchHistoryOut,
    SessionCreate,
    SessionOut,
)
from database.models import ChatMessage, Document, Note, SavedPaper, SearchHistory, Session, get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["memory"])


@router.post("/sessions", response_model=SessionOut)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(id=str(uuid.uuid4()), title=body.title)
    db.add(session)
    await db.flush()
    return session


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.updated_at.desc()))
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}/documents", response_model=list[DocumentOut])
async def get_documents(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document)
        .where(Document.session_id == session_id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return [
        DocumentOut(
            id=d.id,
            title=d.title,
            doc_type=d.doc_type,
            content=d.content,
            citations=d.citations or [],
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.get("/notes", response_model=list[NoteOut])
async def list_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).order_by(Note.updated_at.desc()))
    return result.scalars().all()


@router.post("/notes", response_model=NoteOut)
async def create_note(body: NoteCreate, db: AsyncSession = Depends(get_db)):
    note = Note(
        id=str(uuid.uuid4()),
        title=body.title,
        content=body.content,
        session_id=body.session_id,
    )
    db.add(note)
    await db.flush()
    return note


@router.put("/notes/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, body: NoteCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = body.title
    note.content = body.content
    return note


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note)
    return {"ok": True}


@router.get("/papers", response_model=list[SavedPaperOut])
async def list_papers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedPaper).order_by(SavedPaper.created_at.desc()))
    return result.scalars().all()


@router.post("/papers", response_model=SavedPaperOut)
async def save_paper(body: SavedPaperCreate, db: AsyncSession = Depends(get_db)):
    paper = SavedPaper(
        id=str(uuid.uuid4()),
        title=body.title,
        authors=body.authors,
        url=body.url,
        abstract=body.abstract,
        metadata_json=body.metadata,
    )
    db.add(paper)
    await db.flush()
    return paper


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SavedPaper).where(SavedPaper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    await db.delete(paper)
    return {"ok": True}


@router.get("/search-history", response_model=list[SearchHistoryOut])
async def list_search_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(50))
    return result.scalars().all()
