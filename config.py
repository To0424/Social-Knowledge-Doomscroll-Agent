"""Shared configuration — DB and LLM factory functions."""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────

DB_CONFIG = dict(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    dbname=os.getenv("POSTGRES_DB", "socialscope"),
    user=os.getenv("POSTGRES_USER", "socialscope"),
    password=os.getenv("POSTGRES_PASSWORD", "changeme"),
)


def get_db():
    from db.database import Database
    return Database(**DB_CONFIG)


# ── LLM (Ollama) ─────────────────────────────────────────────────────

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma4:e2b")


def get_llm_client():
    """Return an LLMClient pointing at the local Ollama instance."""
    from llm.client import LLMClient
    return LLMClient(base_url=f"{OLLAMA_BASE_URL}/v1", model=LLM_MODEL)
