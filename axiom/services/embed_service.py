"""LLM semantic embedding engine with Ollama / OpenAI / local fallback (PRD §7.2).

Only vectors ever leave the machine — never raw source. When no provider is
reachable, a deterministic hash-based pseudo-embedding keeps the pipeline alive.
"""
from __future__ import annotations

import hashlib
import logging
import struct
from typing import Sequence

import httpx

from axiom.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = (
    "You are analyzing source code. Describe the semantic purpose and behavior of this "
    "function in terms of: (1) what it does, (2) what external systems it touches, "
    "(3) preconditions, (4) postconditions.\n\n"
    "Function source:\n{source}\n\nFile: {file_path} ({language})\nCalled by: {callers}"
)


class Embedder:
    """Generates and caches semantic embeddings for functions."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = self.settings.embed_provider
        # Circuit breaker: once a provider is unreachable, stop retrying it for the
        # rest of the run so a workspace scan doesn't stall N × connect-timeout.
        self._degraded = False

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single string via the configured provider, with fallbacks."""
        if self._degraded or self.provider == "local":
            return self._embed_fallback(text)
        try:
            if self.provider == "ollama":
                return await self._embed_ollama(text)
            if self.provider == "openai":
                return await self._embed_openai(text)
        except Exception as exc:  # noqa: BLE001 - fall back rather than crash
            self._degraded = True
            logger.warning(
                "Embedding provider '%s' unreachable; using local fallback for this run: %s",
                self.provider,
                exc,
            )
        return self._embed_fallback(text)

    async def embed_batch(self, texts: Sequence[str], batch_size: int = 32) -> list[list[float]]:
        """Embed a batch of strings (sequentially per item; providers vary on batching)."""
        results: list[list[float]] = []
        for text in texts:
            results.append(await self.embed_text(text))
        return results

    def build_prompt(self, source: str, file_path: str, language: str, callers: list[str]) -> str:
        # Long functions get a summarized form to respect model context limits.
        if source.count("\n") > 50:
            source = "\n".join(source.splitlines()[:50]) + "\n# ...(truncated)"
        return PROMPT_TEMPLATE.format(
            source=source, file_path=file_path, language=language, callers=", ".join(callers) or "none"
        )

    # ── Providers ───────────────────────────────────────
    async def _embed_ollama(self, text: str) -> list[float]:
        # Short connect timeout so an absent Ollama trips the breaker fast.
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=1.0)) as client:
            resp = await client.post(
                f"{self.settings.ollama_url}/api/embeddings",
                json={"model": self.settings.ollama_model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]

    async def _embed_openai(self, text: str) -> list[float]:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        if self.settings.air_gapped:
            raise RuntimeError("OpenAI embedding blocked in air-gapped mode")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    @staticmethod
    def _embed_fallback(text: str, dim: int = 768) -> list[float]:
        """Deterministic hash-seeded vector — offline, not semantic, but stable."""
        vec: list[float] = []
        counter = 0
        while len(vec) < dim:
            digest = hashlib.sha256(f"{text}:{counter}".encode()).digest()
            for i in range(0, len(digest), 4):
                if len(vec) >= dim:
                    break
                (val,) = struct.unpack("I", digest[i : i + 4])
                vec.append((val / 0xFFFFFFFF) * 2 - 1)  # normalize to [-1, 1]
            counter += 1
        return vec


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
