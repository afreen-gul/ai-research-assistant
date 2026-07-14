"""Document upload and export endpoints."""

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from agents.citation_agent import build_bibliography
from agents.research_agent import ingest_pdf_for_session
from api.schemas import ExportRequest, PDFUploadResponse
from config import settings
from database.models import get_db
from exports.document_exporter import export_docx, export_markdown, export_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    settings.ensure_dirs()
    file_id = str(uuid.uuid4())
    dest = Path(settings.upload_dir) / f"{file_id}_{file.filename}"

    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        result = ingest_pdf_for_session(session_id, str(dest), file_id)
        return PDFUploadResponse(
            file_id=result["file_id"],
            structured=result["structured"],
            metadata=result["metadata"],
            chunks_ingested=result["chunks_ingested"],
        )
    except Exception as e:
        logger.exception("PDF upload failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_document(request: ExportRequest):
    fmt = request.format.lower()
    bibliography = request.bibliography

    try:
        if fmt == "markdown" or fmt == "md":
            content = export_markdown(request.content, request.title, bibliography)
            return Response(
                content=content,
                media_type="text/markdown",
                headers={"Content-Disposition": f'attachment; filename="{request.title}.md"'},
            )
        elif fmt == "docx":
            content = export_docx(request.content, request.title, bibliography)
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f'attachment; filename="{request.title}.docx"'},
            )
        elif fmt == "pdf":
            content = export_pdf(request.content, request.title, bibliography)
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{request.title}.pdf"'},
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")
    except Exception as e:
        logger.exception("Export failed")
        raise HTTPException(status_code=500, detail=str(e))
