"""Supabase access-token verification.

This project signs tokens asymmetrically (ES256) and publishes its public key
at /auth/v1/.well-known/jwks.json, so the API verifies signatures against the
JWKS rather than holding a shared secret. PyJWKClient caches the key set and
refetches on an unknown `kid`, which is what makes key rotation transparent.

The verified `sub` claim is the ONLY source of the caller's identity. A user id
in a path, query or body is never trusted -- SQLAlchemy connects as a role that
bypasses RLS, so the database will not catch an impersonation attempt.
"""

from __future__ import annotations

from functools import lru_cache

import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from .config import Settings, get_settings


@lru_cache
def _jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


class CurrentUser:
    __slots__ = ("id", "email", "claims")

    def __init__(self, user_id: str, email: str | None, claims: dict):
        self.id = user_id
        self.email = email
        self.claims = claims


def get_current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if settings.disable_auth:
        # Escape hatch for local smoke tests; never enable in deployment.
        return CurrentUser(settings.dev_user_id, None, {"dev": True})

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()

    try:
        signing_key = _jwk_client(settings.jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience=settings.jwt_audience,
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}")
    except Exception as exc:  # JWKS fetch failures, etc.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Cannot verify token: {exc}")

    return CurrentUser(claims["sub"], claims.get("email"), claims)
