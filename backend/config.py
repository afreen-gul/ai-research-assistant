"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    xai_api_key: str = ""
    xai_model: str = "grok-3-mini"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    jwt_secret: str = "change-me-to-a-random-secret-key"
    backend_host: str = "0.0.0.0"
    backend_port: int = int(os.getenv("PORT", "8000"))
    frontend_url: str = (
        os.getenv("FRONTEND_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or os.getenv("PUBLIC_URL")
        or "http://localhost:5173"
    )
    serve_frontend: bool = os.getenv("SERVE_FRONTEND", "").lower() in {"1", "true", "yes"}
    database_url: str = "sqlite+aiosqlite:///./data/research_assistant.db"
    chroma_persist_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_top_k: int = 5
    agent_max_tool_rounds: int = 1
    agent_recursion_limit: int = 12
    agent_timeout_seconds: int = 90

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self) -> None:
        Path(self.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        db_path = self.database_url.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
