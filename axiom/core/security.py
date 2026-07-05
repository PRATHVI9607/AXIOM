"""JWT issuing/verification, API-key hashing, and password helpers.

Uses RS256 when PEM keys are configured (production), else an HS256 dev secret.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from axiom.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


# ── Passwords ────────────────────────────────────────────
def hash_password(password: str) -> str:
    # bcrypt hard-caps input at 72 bytes; truncate deterministically.
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode()[:72], hashed.encode())
    except ValueError:
        return False


# ── API keys ─────────────────────────────────────────────
def generate_api_key() -> tuple[str, str]:
    """Return (plaintext_key, sha256_hash). Store only the hash."""
    raw = "axk_" + secrets.token_urlsafe(32)
    return raw, hash_api_key(raw)


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ── JWT ──────────────────────────────────────────────────
def _signing_key(settings: Settings) -> str:
    return settings.jwt_private_key if settings.use_rs256 else settings.jwt_dev_secret


def _verify_key(settings: Settings) -> str:
    return settings.jwt_public_key if settings.use_rs256 else settings.jwt_dev_secret


def create_access_token(
    subject: str,
    claims: dict[str, Any] | None = None,
    settings: Settings | None = None,
) -> tuple[str, int]:
    """Create a signed access token. Returns (token, expires_in_seconds)."""
    settings = settings or get_settings()
    expires_in = settings.jwt_expiry_hours * 3600
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "type": "access",
        **(claims or {}),
    }
    token = jwt.encode(payload, _signing_key(settings), algorithm=settings.jwt_algorithm)
    return token, expires_in


def create_refresh_token(subject: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_days),
        "type": "refresh",
    }
    return jwt.encode(payload, _signing_key(settings), algorithm=settings.jwt_algorithm)


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt exceptions on failure."""
    settings = settings or get_settings()
    return jwt.decode(token, _verify_key(settings), algorithms=[settings.jwt_algorithm])


# ── FastAPI dependency ───────────────────────────────────
class CurrentUser:
    """Lightweight authenticated principal extracted from a JWT."""

    def __init__(self, sub: str, claims: dict[str, Any]):
        self.sub = sub
        self.username: str = claims.get("username", "")
        self.email: str = claims.get("email", "")
        self.roles: list[str] = claims.get("roles", ["developer"])


LOCAL_PRINCIPAL_CLAIMS = {
    "username": "local",
    "email": "local@axiom.dev",
    "roles": ["admin"],
}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Validate the bearer token and return the principal, or raise 401.

    When `auth_required` is off (default, local single-user mode) every request is
    treated as a local admin so the dashboard/extension work with zero setup.
    """
    if not settings.auth_required:
        return CurrentUser(sub="user:local", claims=LOCAL_PRINCIPAL_CLAIMS)
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, settings)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token")
    return CurrentUser(sub=payload["sub"], claims=payload)
