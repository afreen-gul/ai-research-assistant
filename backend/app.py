"""AI Research Assistant — FastAPI backend entry point."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.auth import router as auth_router
from api.chat import router as chat_router
from api.documents import router as documents_router
from api.sessions import router as sessions_router
from config import settings
from database.models import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Research Assistant Agent",
    description="Agentic research assistant with RAG, web search, and document generation",
    version="1.0.0",
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    origins = {
        settings.frontend_url,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }
    for env_key in ("RENDER_EXTERNAL_URL", "PUBLIC_URL", "FRONTEND_URL"):
        value = os.getenv(env_key, "").strip()
        if value:
            origins.add(value.rstrip("/"))
    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(documents_router)


@app.get("/api/health")
async def health():
    from services.llm_service import get_llm_status

    llm = get_llm_status()
    return {
        "status": "ok",
        "llm_provider": llm["provider"],
        "llm_configured": llm["configured"],
        "model": llm["model"],
        # Kept for older clients
        "gemini_configured": llm["configured"] if llm["provider"] == "gemini" else bool(settings.gemini_api_key),
    }


def _mount_frontend(app: FastAPI) -> None:
    if not settings.serve_frontend or not FRONTEND_DIST.exists():
        return

    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def spa_root():
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")


_mount_frontend(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=settings.backend_host, port=settings.backend_port, reload=True)
