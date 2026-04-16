import pytest
from httpx import AsyncClient


def _db_reachable() -> bool:
    try:
        from app import db

        db.query("SELECT 1 AS ok", one=True)
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not _db_reachable(),
    reason="Set POSTGRES_* in backend/.env and run migrations",
)


@requires_db
@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@requires_db
@pytest.mark.asyncio
async def test_login_create_and_content_flow(client: AsyncClient):
    r = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "demo"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r2 = await client.post("/api/documents", json={"title": "Hello"}, headers=headers)
    assert r2.status_code == 201
    doc_id = r2.json()["id"]
    assert r2.json()["role"] == "owner"

    r3 = await client.get(f"/api/documents/{doc_id}/content", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["content"] is None

    r4 = await client.get("/api/documents", headers=headers)
    assert r4.status_code == 200
    rows = r4.json()
    assert any(d["id"] == doc_id for d in rows)


@requires_db
@pytest.mark.asyncio
async def test_owner_shares_document_with_bob_editor(client: AsyncClient):
    ra = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "demo"},
    )
    rb = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "demo"},
    )
    assert ra.status_code == 200 and rb.status_code == 200
    token_a = ra.json()["access_token"]
    token_b = rb.json()["access_token"]

    created = await client.post(
        "/api/documents",
        json={"title": "Shared doc"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert created.status_code == 201
    doc_id = created.json()["id"]

    sh = await client.post(
        f"/api/documents/{doc_id}/share",
        json={"email": "bob@example.com", "role": "editor"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert sh.status_code == 200
    assert sh.json()["role"] == "editor"

    bob_list = await client.get(
        "/api/documents",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert bob_list.status_code == 200
    rows = bob_list.json()
    match = next((d for d in rows if d["id"] == doc_id), None)
    assert match is not None
    assert match["access"] == "shared"
    assert match["share_role"] == "editor"


@requires_db
@pytest.mark.asyncio
async def test_viewer_cannot_write_content(client: AsyncClient):
    ra = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "demo"},
    )
    rb = await client.post(
        "/api/auth/login",
        json={"email": "bob@example.com", "password": "demo"},
    )
    token_a = ra.json()["access_token"]
    token_b = rb.json()["access_token"]

    created = await client.post(
        "/api/documents",
        json={"title": "RO"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    doc_id = created.json()["id"]
    await client.post(
        f"/api/documents/{doc_id}/share",
        json={"email": "bob@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    body = {"content": {"type": "doc", "content": []}}
    denied = await client.put(
        f"/api/documents/{doc_id}/content",
        json=body,
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert denied.status_code == 403


@requires_db
@pytest.mark.asyncio
async def test_share_link_allows_read_without_login(client: AsyncClient):
    ra = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "demo"},
    )
    token_a = ra.json()["access_token"]
    created = await client.post(
        "/api/documents",
        json={"title": "Link doc"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    doc_id = created.json()["id"]
    lk = await client.post(
        f"/api/documents/{doc_id}/share-link",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert lk.status_code == 200
    secret = lk.json()["token"]

    pub = await client.get(f"/api/documents/link/{secret}")
    assert pub.status_code == 200
    assert pub.json()["access"] == "link"
    assert pub.json()["role"] == "viewer"


@requires_db
@pytest.mark.asyncio
async def test_import_body_replaces_saved_content(client: AsyncClient):
    r = await client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "demo"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/documents", json={"title": "Import target"}, headers=headers)
    assert created.status_code == 201
    doc_id = created.json()["id"]

    put = await client.put(
        f"/api/documents/{doc_id}/content",
        headers=headers,
        json={
            "content": {
                "type": "doc",
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": "before"}]}],
            }
        },
    )
    assert put.status_code == 200

    files = {"file": ("repl.md", b"# replaced\n\nhello", "text/markdown")}
    imp = await client.post(f"/api/documents/{doc_id}/import-body", headers=headers, files=files)
    assert imp.status_code == 200
    body = imp.json()
    assert body["has_content"] is False
    assert "replaced" in (body.get("initial_content") or "")

    content = await client.get(f"/api/documents/{doc_id}/content", headers=headers)
    assert content.status_code == 200
    assert content.json()["content"] is None
