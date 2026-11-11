"""FastAPI application for Game Tracker.

Every endpoint reads from Postgres through SQLAlchemy. Nothing here touches
the JSON files in data/ -- that is the legacy app in `backend/`, which is
still runnable via `./start.sh --legacy`.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routers import ROUTERS


def create_app() -> FastAPI:
    app = FastAPI(
        title="Game Tracker API",
        version="2.0.0",
        description=(
            "Attendance-scoped football statistics read from Postgres. "
            "GET /api/capabilities lists which datasets the schema can answer."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in ROUTERS:
        app.include_router(router)

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "mode": "sql"}

    _mount_static(app)
    return app


class SPAStaticFiles(StaticFiles):
    """Serve the built frontend, falling back to index.html for client-side
    routes (/login, /auth/callback, ...) that have no file on disk.

    The fallback applies to route-like paths only. A request for something
    that looks like a file -- /crests/64/999.png, a stale bundle hash -- gets
    a real 404 instead, because answering those with the HTML shell hides
    broken builds and missing assets behind a 200.
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            # Unmatched API paths stay a real 404, never the SPA shell.
            if path.startswith("api/"):
                raise
            # A dot in the last segment means "asset", not "client route".
            if "." in path.rsplit("/", 1)[-1]:
                raise
            return await super().get_response("index.html", scope)


def _mount_static(app: FastAPI) -> None:
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        app.mount("/", SPAStaticFiles(directory=static_dir, html=True), name="static")


app = create_app()
