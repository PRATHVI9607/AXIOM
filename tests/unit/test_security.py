"""Unit tests for JWT, API-key hashing, and password helpers (PRD §7.13, §12.1)."""
import time

import jwt
import pytest

from axiom.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    hash_password,
    verify_password,
)


def test_access_token_roundtrip():
    token, expires_in = create_access_token("user:1", {"username": "u", "roles": ["admin"]})
    payload = decode_token(token)
    assert payload["sub"] == "user:1"
    assert payload["type"] == "access"
    assert payload["roles"] == ["admin"]
    assert expires_in > 0


def test_refresh_token_typed():
    payload = decode_token(create_refresh_token("user:2"))
    assert payload["type"] == "refresh"


def test_expired_token_rejected():
    from datetime import datetime, timedelta, timezone

    from axiom.core.config import get_settings

    s = get_settings()
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    token = jwt.encode(
        {"sub": "x", "type": "access", "exp": past}, s.jwt_dev_secret, algorithm=s.jwt_algorithm
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)


def test_tampered_token_rejected():
    token, _ = create_access_token("user:1")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token + "tamper")


def test_api_key_hash_stable_and_prefixed():
    raw, h = generate_api_key()
    assert raw.startswith("axk_")
    assert h == hash_api_key(raw)
    assert len(h) == 64  # sha256 hex


def test_password_hash_verify():
    h = hash_password("s3cret")
    assert h != "s3cret"
    assert verify_password("s3cret", h)
    assert not verify_password("wrong", h)
