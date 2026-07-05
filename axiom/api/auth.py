"""Auth endpoints: GitHub OAuth flow, local login, token refresh, API keys (PRD §8.5)."""
from __future__ import annotations

import logging

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.core.config import Settings, get_settings
from axiom.core.database import get_db
from axiom.core.security import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    get_current_user,
    verify_password,
)
from axiom.models.api_models import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    LocalLoginRequest,
    TokenResponse,
    UserOut,
)
from axiom.models.db_models import ApiKey, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"


def _issue_tokens(user: User) -> TokenResponse:
    access, expires_in = create_access_token(
        subject=f"user:{user.id}",
        claims={"username": user.username, "email": user.email, "roles": [user.role]},
    )
    refresh = create_refresh_token(subject=f"user:{user.id}")
    return TokenResponse(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.get("/login")
async def login(settings: Settings = Depends(get_settings)) -> RedirectResponse:
    """Redirect the browser to GitHub's OAuth consent screen."""
    if settings.auth_provider != "github" or not settings.github_client_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "GitHub OAuth not configured")
    redirect_uri = f"{settings.base_url}/api/v1/auth/callback"
    url = (
        f"{GITHUB_AUTHORIZE}?client_id={settings.github_client_id}"
        f"&redirect_uri={redirect_uri}&scope=read:user%20user:email"
    )
    return RedirectResponse(url)


@router.get("/callback", response_model=TokenResponse)
async def callback(
    code: str,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange the GitHub code for a token, upsert the user, issue AXIOM JWTs."""
    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            GITHUB_TOKEN,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        access = token_resp.json().get("access_token")
        if not access:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "GitHub token exchange failed")
        user_resp = await client.get(
            GITHUB_USER, headers={"Authorization": f"Bearer {access}"}
        )
        gh = user_resp.json()

    github_id = str(gh["id"])
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            github_id=github_id,
            username=gh.get("login", "unknown"),
            email=gh.get("email") or f"{gh.get('login')}@users.noreply.github.com",
            role="developer",
        )
        db.add(user)
        await db.flush()
    return _issue_tokens(user)


@router.post("/local", response_model=TokenResponse)
async def local_login(
    body: LocalLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Local password login (air-gapped mode / no OAuth)."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a fresh access token from a valid refresh token."""
    try:
        payload = decode_token(refresh_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc
    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    user_id = payload["sub"].removeprefix("user:")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return _issue_tokens(user)


@router.get("/me", response_model=UserOut)
async def me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """Return the authenticated user's profile."""
    user = await db.get(User, current.sub.removeprefix("user:"))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserOut(id=user.id, username=user.username, email=user.email, role=user.role)


@router.post("/apikeys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    """Create a CI/CD API key. The plaintext key is returned exactly once."""
    raw, key_hash = generate_api_key()
    api_key = ApiKey(
        user_id=current.sub.removeprefix("user:"),
        project_id=body.project_id,
        key_hash=key_hash,
        name=body.name,
    )
    db.add(api_key)
    await db.flush()
    return ApiKeyCreateResponse(id=api_key.id, name=api_key.name, api_key=raw)
