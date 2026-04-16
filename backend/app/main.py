from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.keepalive import start_keepalive, stop_keepalive
from app.routers import auth, documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
_log = logging.getLogger("ajaia.api")


class _LogUnhandledErrorsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            _log.exception("%s %s", request.method, request.url.path)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched = start_keepalive()
    try:
        try:
            from app import db

            db.init_db()
            db.query("SELECT 1 AS ok", one=True)
            _log.info("database: ok (SELECT 1)")
        except Exception:
            _log.exception(
                "database: startup check failed — set POSTGRES_* on Render and PGSSLMODE=require for Supabase"
            )
        yield
    finally:
        stop_keepalive(sched)


app = FastAPI(title="Ajaia Docs API", version="0.1.0", lifespan=lifespan)

# Always allow local dev + production UI (Render env CORS_ORIGINS is merged, not a full replace).
_BUILTIN_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://ajaia-ai-native-docs-editor.vercel.app",
)


def _cors_origins() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for o in _BUILTIN_CORS_ORIGINS:
        if o not in seen:
            seen.add(o)
            out.append(o)
    extra = os.getenv("CORS_ORIGINS", "").strip()
    if extra:
        for o in extra.split(","):
            o = o.strip()
            if o and o not in seen:
                seen.add(o)
                out.append(o)
    return out


_cors = _cors_origins()

app.add_middleware(_LogUnhandledErrorsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
