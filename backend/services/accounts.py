"""Removal of abandoned, unregistered auth users.

Google OAuth creates the auth.users row before the client gets any say: by the
time the callback runs, GoTrue has already inserted it. So an unregistered
sign-in attempt cannot be *prevented* in the browser, only undone.

Supabase's "before user created" auth hook is the only true prevention, and it
cannot help here: OAuth carries no sign-in-vs-sign-up intent, so a hook could
only reject every new account, not the ones that took the wrong door.

This module therefore cleans up after the fact, under two deliberate limits:
  * it only ever acts on the caller's own id, taken from the verified token;
  * it refuses when a profiles row exists, so a real account is unreachable.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Profile


class AccountDeletionError(RuntimeError):
    pass


def is_registered(session: Session, user_id: str) -> bool:
    """Registration is defined by a profiles row, not an auth.users row."""
    return session.execute(
        sa.select(sa.func.count()).select_from(Profile).where(Profile.user_id == user_id)
    ).scalar() > 0


def delete_auth_user(user_id: str, timeout: float = 15.0) -> None:
    """Delete an auth user via the GoTrue admin API.

    Uses the service_role key, so the caller MUST have already established
    that this is the token owner's own unregistered account.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise AccountDeletionError(
            "SUPABASE_URL / SUPABASE_SECRET_KEY are not configured"
        )

    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{user_id}"
    request = urllib.request.Request(url, method="DELETE")
    request.add_header("apikey", settings.supabase_secret_key)
    request.add_header("Authorization", f"Bearer {settings.supabase_secret_key}")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status not in (200, 204):
                raise AccountDeletionError(f"GoTrue returned {response.status}")
    except urllib.error.HTTPError as exc:
        # 404 means it is already gone, which satisfies the caller's intent.
        if exc.code == 404:
            return
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise AccountDeletionError(f"GoTrue {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AccountDeletionError(f"Cannot reach GoTrue: {exc.reason}") from exc
