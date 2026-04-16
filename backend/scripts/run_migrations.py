"""Apply numbered SQL migrations in backend/migrations/."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Must match SQL migrations (ajaia.*) and app db.py POSTGRES_SCHEMA.
MIGRATION_SCHEMA = os.getenv("POSTGRES_SCHEMA", "ajaia").strip() or "ajaia"

from app.db import get_db  # noqa: E402


def main() -> None:
    mig_dir = ROOT / "migrations"
    files = sorted(mig_dir.glob("*.sql"))
    if not files:
        print("No migrations found.")
        return

    sch = sql.Identifier(MIGRATION_SCHEMA)
    with get_db() as conn:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sch))
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {}.schema_migrations (
                    id TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            ).format(sch)
        )
        cur.close()

    for path in files:
        mid = path.name
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                sql.SQL("SELECT 1 FROM {}.schema_migrations WHERE id = %s").format(sch),
                (mid,),
            )
            if cur.fetchone():
                cur.close()
                print(f"skip {mid}")
                continue
            cur.close()
        body = path.read_text(encoding="utf-8")
        with get_db() as conn:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(body)
            cur.close()
        with get_db() as conn:
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(
                sql.SQL("INSERT INTO {}.schema_migrations (id) VALUES (%s)").format(sch),
                (mid,),
            )
            cur.close()
        print(f"applied {mid}")


if __name__ == "__main__":
    main()
