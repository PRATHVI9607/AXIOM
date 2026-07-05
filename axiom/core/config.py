"""Central application settings loaded from environment / .env (pydantic-settings)."""
from __future__ import annotations

import sys
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All AXIOM configuration. Access via `get_settings()`, never `os.environ`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Database ─────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./.axiom/axiom.db",
        alias="DATABASE_URL",
    )

    # ── ChromaDB ─────────────────────────────────────────
    chroma_url: str = Field(default="http://localhost:8001", alias="CHROMA_URL")

    # ── Embedding ────────────────────────────────────────
    embed_provider: Literal["ollama", "openai", "local"] = Field(
        default="ollama", alias="AXIOM_EMBED_PROVIDER"
    )
    ollama_url: str = Field(default="http://localhost:11434", alias="AXIOM_OLLAMA_URL")
    ollama_model: str = Field(default="nomic-embed-text", alias="AXIOM_OLLAMA_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # ── Auth ─────────────────────────────────────────────
    jwt_private_key: str = Field(default="", alias="AXIOM_JWT_PRIVATE_KEY")
    jwt_public_key: str = Field(default="", alias="AXIOM_JWT_PUBLIC_KEY")
    jwt_dev_secret: str = Field(
        default="axiom-dev-only-secret-change-me-32bytes+", alias="AXIOM_JWT_DEV_SECRET"
    )
    jwt_expiry_hours: int = 24
    jwt_refresh_days: int = 7
    github_client_id: str = Field(default="", alias="GITHUB_CLIENT_ID")
    github_client_secret: str = Field(default="", alias="GITHUB_CLIENT_SECRET")
    auth_provider: Literal["github", "local"] = Field(default="github", alias="AXIOM_AUTH_PROVIDER")

    # ── eBPF ─────────────────────────────────────────────
    ebpf_enabled: bool = Field(default=True, alias="AXIOM_EBPF_ENABLED")
    # Address of the privileged tracer daemon (runs in WSL/Linux). The API is a
    # client to this over localhost; WSL2 forwards localhost to Windows.
    ebpf_tracer_host: str = Field(default="127.0.0.1", alias="AXIOM_EBPF_TRACER_HOST")
    ebpf_tracer_port: int = Field(default=8770, alias="AXIOM_EBPF_TRACER_PORT")

    # ── Deployment ───────────────────────────────────────
    base_url: str = Field(default="http://localhost:8000", alias="AXIOM_BASE_URL")
    frontend_url: str = Field(default="http://localhost:3000", alias="AXIOM_FRONTEND_URL")
    log_level: str = Field(default="INFO", alias="AXIOM_LOG_LEVEL")
    air_gapped: bool = Field(default=False, alias="AXIOM_AIR_GAPPED")

    # ── Derived / computed properties ────────────────────
    @property
    def use_rs256(self) -> bool:
        """True when RS256 PEM keys are configured; otherwise HS256 dev fallback."""
        return bool(self.jwt_private_key.strip() and self.jwt_public_key.strip())

    @property
    def jwt_algorithm(self) -> str:
        return "RS256" if self.use_rs256 else "HS256"

    @property
    def ebpf_native(self) -> bool:
        """True when the API process itself runs on Linux and can load probes directly."""
        return self.ebpf_enabled and sys.platform.startswith("linux")

    @property
    def ebpf_available(self) -> bool:
        """eBPF is available either natively (Linux API) or via the WSL tracer daemon.

        On Windows the API reaches a real Linux kernel through the tracer running
        in WSL, so eBPF is considered available whenever tracing is enabled.
        """
        return self.ebpf_enabled


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()
