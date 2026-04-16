from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.keepalive import start_keepalive, stop_keepalive
from app.routers import auth, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched = start_keepalive()
    try:
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
