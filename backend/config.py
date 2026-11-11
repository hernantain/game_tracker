"""Runtime settings, loaded from the environment (.env at the repo root)."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # Postgres connection string (database password, not the API key).
    database_url: str = ""
    # Used to derive the JWKS URL that validates Supabase access tokens.
    supabase_url: str = ""
    # service_role key. Needed only to delete an abandoned, unregistered auth
    # user -- see services/accounts.py. Never sent to the browser.
    supabase_secret_key: str = ""
    # Audience claim GoTrue puts on access tokens.
    jwt_audience: str = "authenticated"
    # Local-only escape hatch: skip JWT verification and act as `dev_user_id`.
    # Intended for smoke-testing the data path without a browser round-trip.
    # Never enable in a deployed environment -- it disables authentication.
    disable_auth: bool = False
    dev_user_id: str = "00000000-0000-0000-0000-000000000000"

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
