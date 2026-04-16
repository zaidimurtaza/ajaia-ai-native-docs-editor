# Submission package — Ajaia AI-Native Full Stack Assignment

**Candidate:** Murtaza Zaidi (zaidimurtaza102@gmail.com)

## Included in this repository

| Item | Location |
|------|----------|
| Source code | `backend/`, `ui/` |
| Local setup | `README.md` |
| Architecture note | `ARCHITECTURE.md` |
| AI workflow note | `AI_WORKFLOW.md` |
| Walkthrough video URL (placeholder) | `VIDEO_URL.txt` |
| Database migrations | `backend/migrations/001_initial.sql` |
| Automated tests | `backend/tests/test_api.py` |

## Reviewer checklist

1. Apply `backend/migrations/001_initial.sql` in Supabase (or run `backend/scripts/run_migrations.py`).
2. Configure `backend/.env` with `POSTGRES_*` (and `PGSSLMODE=require` for Supabase).
3. Run backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000` from `backend/`.
4. Run UI: `npm run dev` from `ui/` (proxies to backend on localhost).
5. Sign in as **alice@example.com** / **demo** or **bob@example.com** / **demo**; share a doc from Alice to Bob to verify sharing.

## Live deployment

Add your public API and UI URLs here when deployed (also update `README.md` and replace `VIDEO_URL.txt` with your Loom/YouTube link).

- **App URL:** _(add after deploy)_
- **API URL:** _(add after deploy)_

## Partial / next steps

See **README.md** section *Assignment status* for what is intentionally scoped vs. what would come next with more time.
