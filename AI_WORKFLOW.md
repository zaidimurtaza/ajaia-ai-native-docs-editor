# AI workflow note

## Tools

- **Cursor** (agent chat + inline edits) for scaffolding, refactors, and repetitive file creation.
- **AI-assisted reasoning** for tradeoffs (e.g., Yjs relay vs. full y-websocket server) and for tightening copy in submission docs.

## Where AI sped things up

- Bootstrapping the **folder layout**, **FastAPI routers**, and **Vite + TipTap + Yjs** wiring.
- Drafting **README**, **SUBMISSION**, and **architecture** text from the actual code paths.
- Generating **pytest** flows once the API surface was stable.

## What was changed or rejected

- **Rejected:** realtime WebSocket / Yjs sync for this slice — replaced with REST + RBAC to match scope.
- **Changed:** simplified attachment downloads to **authenticated fetch + blob** instead of tokenized public URLs.
- **Tightened:** DB access pattern to match an existing **psycopg2 pool + `query()`** style for consistency with prior work.

## Verification

- **Correctness:** `pytest` against a real Postgres instance after migrations; manual multi-tab edit to confirm Yjs relay + reload preserves content.
- **UX:** toolbar for bold/italic/underline/headings/lists; clear owned vs. shared badges; explicit import file-type limits in UI + README.
- **Reliability:** debounced Yjs persist; WebSocket cleanup on unmount; CORS driven by env for deployed origins.
