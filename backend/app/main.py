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

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_cors = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

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
