# Architecture note

## What we prioritized

1. **Document lifecycle** — create, rename (owner only), rich edit, autosave to Postgres as **TipTap JSON** (`documents.content_json`).
2. **RBAC** — **Owner** (full control), **Editor** (body + attachments), **Viewer** (read body + download attachments). Invites are per-user; **anyone-with-link** uses a secret token and a chosen link role (viewer or editor).
3. **No realtime transport** — no WebSocket; saves are debounced HTTP `PUT`. Simpler to deploy and sufficient for the brief.
4. **Sharing** — `document_shares(role)` plus optional `documents.share_token` / `share_token_role`.

## Stack

- **Backend:** FastAPI, psycopg2 pool + `query()`, bcrypt passwords.
- **DB:** PostgreSQL (Supabase-compatible); SQL migrations `001`–`003`.
- **Frontend:** Vite, React (JSX), TipTap (StarterKit + Underline).

## Deliberate non-goals

Live cursors, OT/CRDT sync, `.docx` import, anonymous attachment upload (attachments require a signed-in editor/owner).
