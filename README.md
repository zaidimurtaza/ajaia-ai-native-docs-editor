# Ajaia Docs (assignment)

Collaborative rich-text documents with **FastAPI**, **Postgres (Supabase)**, and **Vite + React (JSX)** — autosave over REST, RBAC, and optional share links.

## Prerequisites

- Python 3.11+
- Node 20+
- A [Supabase](https://supabase.com) project (free tier is fine)

## Supabase database

All app tables are in the **`ajaia`** schema (not `public`). The API sets `search_path=ajaia,public` on each connection. Optional env: `POSTGRES_SCHEMA` (default `ajaia`) must match the schema used in the migration SQL files.

1. In the Supabase dashboard: **Project Settings → Database** — note host, port, database name, user, and password.
2. Create `backend/.env` (same shape as `backend/.env.example`):

```env
POSTGRES_HOST=aws-0-[region].pooler.supabase.com
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.[project-ref]
POSTGRES_PASSWORD=your-password
PGSSLMODE=require
```

## Migrations

Apply SQL once (either option):

**A. Supabase SQL Editor** — run in order: `001_initial.sql`, `002_seed_passwords_bcrypt.sql` (if you had plaintext passwords), `003_rbac_and_content_json.sql`.

**B. Local script** (from repo root):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy .env.example .env   # then set POSTGRES_* (and PGSSLMODE for Supabase)
python scripts/run_migrations.py
```

## Run backend

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run UI

The UI is **React + JSX** (no TypeScript).

```bash
cd ui
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite dev server proxies `/api` to the backend.

## Seeded users (after migration)

Passwords are stored with **bcrypt** (cost 12). Demo login is still:

| Email              | Password |
| ------------------ | -------- |
| `alice@example.com` | `demo`   |
| `bob@example.com`   | `demo`   |

If you previously ran an older migration with plaintext passwords, run migrations again so `002_seed_passwords_bcrypt.sql` applies.

## Tests

```bash
cd backend
pytest
```

Requires `POSTGRES_*` in `backend/.env` and applied migrations.

## Assignment status (brief)

| Area | Status |
|------|--------|
| Create / rename / edit / save / reopen | Working (Yjs + TipTap; toolbar for bold, italic, underline, H1/H2, lists) |
| File upload | New doc from `.txt`/`.md`/`.markdown`; import-into-draft; attachments (limits in UI + README) |
| Sharing | Owner invites **viewer** or **editor**; optional **anyone-with-link** (`/link/…`) as viewer or editor |
| Persistence | Postgres; TipTap document JSON in `content_json` |
| Tests | `pytest` — health, login+create, share flow |
| Deprioritized | `.docx`, OT server, comments, version history, presence cursors |

**Next 2–4h:** `.docx` import (e.g. mammoth), export Markdown, basic presence.

## Submission deliverables

- `SUBMISSION.md` — package index
- `ARCHITECTURE.md` — priorities and tradeoffs
- `AI_WORKFLOW.md` — how AI was used
- `VIDEO_URL.txt` — replace with your walkthrough link

## Deployment (reviewers)

Free-tier friendly pattern:

1. **Database:** Supabase Postgres (run migration SQL once).
2. **API:** e.g. Render/Railway/Fly — set `POSTGRES_*`, `PGSSLMODE`, `CORS_ORIGINS` (your static site origin).
3. **UI:** e.g. Vercel/Netlify — build `ui/` with `VITE_API_BASE_URL=https://your-api.example.com`.

## Scope notes

### Files (also summarized in the UI sidebar)

| Flow | Supported types | Notes |
|------|-----------------|--------|
| **New document from file** | UTF-8 `.txt`, `.md`, `.markdown` | Sidebar button or drag-and-drop on the main pane; title = filename stem. **Not supported:** `.docx` or other binary formats. |
| **Attachment** | Any type | Up to **5 MB** per file; stored for download; **does not** become editor text. |
| **Import into open draft** | UTF-8 `.txt`, `.md`, `.markdown` | Replaces saved body; clears TipTap JSON; title unchanged. **Not:** `.docx`. |

- **Auth:** Passwords hashed with **bcrypt**; bearer token is the user UUID (assignment scope).
- **RBAC:** Owner manages title, invites, and links. **Editor** can change body, import text into the draft, and upload attachments. **Viewer** is read-only for the doc body (attachments readable).
