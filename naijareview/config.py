"""Centralised configuration via Pydantic Settings.

All environment variables are loaded from .env (or system env) and
validated at startup. Import ``settings`` from this module anywhere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings, sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ─── Gemini ───────────────────────────────────
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_generation_model: str = "gemini-2.5-pro"
    gemini_utility_model: str = "gemini-2.0-flash"

    # ─── LLM Call Configuration ───────────────────
    llm_max_retries: int = 2
    llm_default_temperature: float = 0.7
    llm_max_tokens: int = 1000

    # ─── Database ─────────────────────────────────
    database_url: str = "sqlite:///./data/naijareview.db"

    # ─── Auth / JWT ───────────────────────────────
    jwt_secret_key: str = Field(..., description="Secret key for JWT signing")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # ─── ChromaDB ─────────────────────────────────
    chroma_persist_dir: Path = Path("./data/chroma")
    chroma_collection_prefix: str = "naijareview"

    # ─── FAISS ────────────────────────────────────
    faiss_index_path: Path = Path("./data/processed/faiss_index")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ─── Redis (Fingerprint Cache) ────────────────
    redis_url: str = "redis://localhost:6379/0"
    fingerprint_cache_ttl_hours: int = 24
    cache_backend: Literal["redis", "memory"] = "memory"

    # ─── API Server ───────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    log_level: str = "DEBUG"

    # ─── Vibe Checker Thresholds ──────────────────
    vibe_regen_threshold: float = 0.70
    vibe_max_retries: int = 2

    # ─── Retrieval ────────────────────────────────
    retrieval_top_k: int = 20
    bm25_weight: float = 0.4
    semantic_weight: float = 0.6

    # ─── Evaluation ───────────────────────────────
    eval_sample_size: int = 1000
    eval_seed: int = 42
    results_dir: Path = Path("./results")

    # ─── Confidence Thresholds ────────────────────
    task_b_confidence_threshold: float = 0.75
    min_diversity_score: float = 0.6
    min_history_for_fingerprint: int = 3


# Singleton instance — import this everywhere
settings = Settings()
