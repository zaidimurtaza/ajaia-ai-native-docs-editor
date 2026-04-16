"""Database connection with pooling"""
import os
import uuid
from contextlib import contextmanager

from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

load_dotenv()

_pool = None

# App tables live in this schema (see migrations). Must match POSTGRES_SCHEMA / migrations.
DEFAULT_SCHEMA = "ajaia"
SCHEMA = os.getenv("POSTGRES_SCHEMA", DEFAULT_SCHEMA).strip() or DEFAULT_SCHEMA


def tbl(name: str) -> str:
    """Qualified table name so we never accidentally hit public.* with the same basename."""
    return f"{SCHEMA}.{name}"


def as_uuid(value) -> uuid.UUID:
    """RealDictCursor often returns UUID columns as str; normalize for comparisons."""
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _connect_kwargs():
    # public last so extension functions (e.g. pgcrypto) still resolve; app tables are always qualified.
    search_path = f"-c search_path={SCHEMA},public"
    kw = dict(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT") or "5432",
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        options=search_path,
    )
    sslmode = os.getenv("PGSSLMODE", "").strip()
    if sslmode:
        kw["sslmode"] = sslmode
    return kw


def init_db():
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(2, 10, **_connect_kwargs())


@contextmanager
def get_db():
    init_db()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


def query(sql, params=None, one=False):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(sql, params)
            if cur.description:
                row = cur.fetchone() if one else cur.fetchall()
                conn.commit()
                if one:
                    return dict(row) if row else None
                return [dict(r) for r in row]
            conn.commit()
            return cur.rowcount
        except Exception:
            conn.rollback()
            raise
