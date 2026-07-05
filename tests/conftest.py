"""Shared pytest fixtures: isolated SQLite DB + authenticated TestClient."""
from __future__ import annotations

import os
import tempfile

import pytest

# Point the app at a throwaway SQLite DB before any axiom import reads settings.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp}/test.db"
os.environ["AXIOM_JWT_DEV_SECRET"] = "test-secret-key-that-is-long-enough-32b"
os.environ["AXIOM_EBPF_ENABLED"] = "false"
# Exercise the real auth path in tests (product default is auth-off local mode).
os.environ["AXIOM_AUTH_REQUIRED"] = "true"


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create tables once for the whole test session."""
    import asyncio

    from axiom.core.database import Base, engine
    from axiom.models import db_models  # noqa: F401 - register tables

    async def _init() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_init())
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from axiom.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    from axiom.core.security import create_access_token

    token, _ = create_access_token(
        "user:test", {"username": "tester", "email": "t@axiom.dev", "roles": ["admin"]}
    )
    return {"Authorization": f"Bearer {token}"}
