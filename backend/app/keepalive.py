"""Background job: ping public health URL so free hosts (e.g. Render) stay warm."""

from __future__ import annotations

import logging
import os

import requests
from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _resolve_health_url() -> str | None:
    explicit = os.getenv("KEEPALIVE_HEALTH_URL", "").strip()
    if explicit:
        return explicit
    # Render injects this for web services
    base = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if base:
        return f"{base.rstrip('/')}/api/health"
    return None


def _ping_health(url: str) -> None:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        logger.warning("keepalive health ping failed: %s", e)


def start_keepalive() -> BackgroundScheduler | None:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    url = _resolve_health_url()
    if not url:
        logger.info(
            "keepalive disabled (set KEEPALIVE_HEALTH_URL or deploy on Render with RENDER_EXTERNAL_URL)"
        )
        return None
    sched = BackgroundScheduler()
    sched.add_job(
        lambda: _ping_health(url),
        "interval",
        minutes=2,
        id="health_keepalive",
        replace_existing=True,
    )
    sched.start()
    _ping_health(url)
    _scheduler = sched
    logger.info("keepalive: GET %s every 2 minutes", url)
    return sched


def stop_keepalive(sched: BackgroundScheduler | None) -> None:
    global _scheduler
    if sched is not None:
        sched.shutdown(wait=False)
    _scheduler = None
