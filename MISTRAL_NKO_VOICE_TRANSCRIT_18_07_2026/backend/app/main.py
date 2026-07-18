"""Application entrypoint: middleware, rate limiting, routers, static UI."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api import auth, health, tools, transcriptions
from app.config import get_settings
from app.limits import limiter
from app.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

STATIC_DIR = Path(__file__).parent / "static"


def _rate_limit_handler(request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


def create_app() -> FastAPI:
    get_settings()  # fail fast on invalid configuration (e.g. short secret)
    app = FastAPI(title="N'Ko Voice Transcriptor API", version=__version__)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    # Order matters: added last = outermost. Body limit runs before parsing;
    # headers wrap every response including errors.
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(transcriptions.router, prefix="/api/v1")
    app.include_router(tools.router, prefix="/api/v1")

    try:  # optional observability
        from prometheus_client import make_asgi_app

        app.mount("/metrics", make_asgi_app())
    except ImportError:  # pragma: no cover
        pass

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", include_in_schema=False)
        def index():
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
