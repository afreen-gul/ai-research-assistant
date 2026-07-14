"""Chat and agent endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.citation_agent import build_bibliography
from agents.research_agent import ResearchAgent, ingest_pdf_for_session
from agents.review_agent import ReviewAgent
from agents.writing_agent import WritingAgent
from api.schemas import ChatRequest, ChatResponse, PDFUploadResponse
from database.models import ChatMessage, Document, SearchHistory, Session, get_db
from services.llm_service import MissingAPIKeyError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _classify_llm_error(e: Exception) -> HTTPException:
    """Map agent/LLM exceptions to clean, user-facing HTTP errors."""
    if isinstance(e, MissingAPIKeyError):
        return HTTPException(status_code=400, detail=str(e))
    msg = str(e).lower()
    if any(t in msg for t in ("quota", "resource_exhausted", "429", "rate limit", "ratelimit")):
        if "limit: 0" in msg or "limit:0" in msg:
            return HTTPException(
                status_code=429,
                detail=(
                    "This model has no free-tier quota on your API key. "
                    "Try another LLM_PROVIDER in .env (groq, xai, or openai) and restart the backend."
                ),
            )
        return HTTPException(
            status_code=429,
            detail="LLM API quota or rate limit reached. Please wait a minute and try again.",
        )
    if any(t in msg for t in ("api key", "api_key", "permission", "unauthenticated", "credentials", "invalid")):
        return HTTPException(
            status_code=400,
            detail="LLM API key is invalid or not authorized. Check your provider API key in .env.",
        )
    return HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    session_id = request.session_id
    if not session_id:
        session = Session(id=str(uuid.uuid4()), title=request.message[:80])
        db.add(session)
        await db.flush()
        session_id = session.id
    else:
        result = await db.execute(select(Session).where(Session.id == session_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Session not found")

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    history_msgs = history_result.scalars().all()
    history = [{"role": m.role, "content": m.content} for m in history_msgs]

    user_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    search_entry = SearchHistory(
        id=str(uuid.uuid4()),
        session_id=session_id,
        query=request.message,
    )
    db.add(search_entry)

    agent = ResearchAgent()
    try:
        result = await agent.run(session_id, request.message, history)
    except Exception as e:
        logger.exception("Agent run failed")
        raise _classify_llm_error(e)

    response_text = result["response"]
    sources = result["sources"]
    tool_events = result["tool_events"]
    document_data = None

    search_entry.results_count = str(len(sources))

    doc_request = result.get("document_request")
    if doc_request and doc_request.get("requested"):
        doc_type = doc_request.get("type", "summary")
        try:
            logger.info("Gemini call: writing agent (%s)", doc_type)
            writer = WritingAgent()
            draft = await writer.draft(
                doc_type=doc_type,
                topic=request.message,
                sources=sources,
                research_findings=response_text,
                citation_style=request.citation_style,
            )
            logger.info("Gemini call: review agent")
            reviewer = ReviewAgent()
            polished = await reviewer.review(draft["content"])
        except Exception as e:
            logger.exception("Document generation failed")
            raise _classify_llm_error(e)
        bibliography = build_bibliography(sources, request.citation_style)

        doc = Document(
            id=str(uuid.uuid4()),
            session_id=session_id,
            title=draft["title"],
            doc_type=doc_type,
            content=polished,
            citations=bibliography,
        )
        db.add(doc)
        document_data = {
            "id": doc.id,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "content": polished,
            "citations": bibliography,
        }

    assistant_msg = ChatMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=response_text,
        tool_events=tool_events,
    )
    db.add(assistant_msg)

    return ChatResponse(
        session_id=session_id,
        message_id=assistant_msg.id,
        response=response_text,
        tool_events=tool_events,
        sources=sources,
        document=document_data,
    )


@router.post("/upload-pdf", response_model=PDFUploadResponse)
async def upload_pdf(
    session_id: str,
    file_path: str = "",
    db: AsyncSession = Depends(get_db),
):
    raise HTTPException(status_code=400, detail="Use /api/documents/upload instead")
