from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from psycopg2.extras import Json

from app import db
from app.deps import current_user_id, optional_user_id
from app.schemas import (
    AttachmentOut,
    DocumentContentIn,
    DocumentContentOut,
    DocumentCreate,
    DocumentDetail,
    DocumentRename,
    DocumentSummary,
    ShareIn,
    ShareLinkIn,
    ShareLinkOut,
    ShareOut,
    UserListItem,
    UserOut,
)
from app.services import access

router = APIRouter(prefix="/documents", tags=["documents"])

U = db.tbl("users")
DOC = db.tbl("documents")
SH = db.tbl("document_shares")
ATT = db.tbl("document_attachments")

_TEXT_IMPORT = {".txt", ".md", ".markdown"}


def _touch_document(doc_id: uuid.UUID) -> None:
    db.query(
        f"UPDATE {DOC} SET updated_at = %s WHERE id = %s",
        (datetime.now(timezone.utc), str(doc_id)),
    )


def _access_label(document_id: uuid.UUID, user_id: uuid.UUID | None, acc: access.DocumentAccess) -> str:
    if acc.role == "owner":
        return "owner"
    if user_id is not None:
        row = db.query(
            f"""
            SELECT 1 FROM {SH}
            WHERE document_id = %s AND user_id = %s
            LIMIT 1
            """,
            (str(document_id), str(user_id)),
            one=True,
        )
        if row:
            return "shared"
    return "link"


def _detail_from_row(row: dict, acc: access.DocumentAccess, user_id: uuid.UUID | None) -> DocumentDetail:
    return DocumentDetail(
        id=row["id"],
        title=row["title"],
        owner_id=row["owner_id"],
        access=_access_label(row["id"], user_id, acc),
        role=acc.role,
        updated_at=row["updated_at"],
        initial_content=row.get("initial_content"),
        has_content=row.get("content_json") is not None,
    )


def _fetch_doc_row(document_id: uuid.UUID) -> dict | None:
    return db.query(
        f"""
        SELECT id, title, owner_id, updated_at, initial_content, content_json
        FROM {DOC}
        WHERE id = %s
        LIMIT 1
        """,
        (str(document_id),),
        one=True,
    )


# --- Link-first routes (string token, not UUID) ---


@router.get("/link/{share_token}", response_model=DocumentDetail)
def get_document_by_link(
    share_token: str,
    user_id: uuid.UUID | None = Depends(optional_user_id),
) -> DocumentDetail:
    row = db.query(
        f"""
        SELECT id, title, owner_id, updated_at, initial_content, content_json
        FROM {DOC}
        WHERE share_token IS NOT NULL AND share_token = %s
        LIMIT 1
        """,
        (share_token,),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(row["id"], user_id, share_token)
    access.require(acc, "read")
    return _detail_from_row(row, acc, user_id)


@router.get("/link/{share_token}/content", response_model=DocumentContentOut)
def get_content_by_link(
    share_token: str,
    user_id: uuid.UUID | None = Depends(optional_user_id),
) -> DocumentContentOut:
    row = db.query(
        f"SELECT id FROM {DOC} WHERE share_token IS NOT NULL AND share_token = %s LIMIT 1",
        (share_token,),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(row["id"], user_id, share_token)
    access.require(acc, "read")
    return _get_content_row(row["id"])


@router.put("/link/{share_token}/content", response_model=DocumentContentOut)
def put_content_by_link(
    share_token: str,
    body: DocumentContentIn,
    user_id: uuid.UUID | None = Depends(optional_user_id),
) -> DocumentContentOut:
    row = db.query(
        f"SELECT id FROM {DOC} WHERE share_token IS NOT NULL AND share_token = %s LIMIT 1",
        (share_token,),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(row["id"], user_id, share_token)
    access.require(acc, "write_content")
    return _save_content(row["id"], body.content)


def _get_content_row(document_id: uuid.UUID) -> DocumentContentOut:
    row = db.query(
        f"SELECT content_json FROM {DOC} WHERE id = %s LIMIT 1",
        (str(document_id),),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    cj = row["content_json"]
    if cj is None:
        return DocumentContentOut(content=None)
    if isinstance(cj, dict):
        return DocumentContentOut(content=cj)
    return DocumentContentOut(content=dict(cj))


def _save_content(document_id: uuid.UUID, content: dict) -> DocumentContentOut:
    db.query(
        f"""
        UPDATE {DOC}
        SET content_json = %s, updated_at = %s, initial_content = NULL
        WHERE id = %s
        """,
        (Json(content), datetime.now(timezone.utc), str(document_id)),
    )
    return DocumentContentOut(content=content)


@router.get("", response_model=list[DocumentSummary])
def list_documents(user_id: uuid.UUID = Depends(current_user_id)) -> list[DocumentSummary]:
    rows = db.query(
        f"""
        SELECT d.id, d.title, d.owner_id, d.updated_at,
               CASE WHEN d.owner_id = %s THEN 'owner' ELSE 'shared' END AS access,
               s.role AS share_role
        FROM {DOC} d
        LEFT JOIN {SH} s ON s.document_id = d.id AND s.user_id = %s
        WHERE d.owner_id = %s OR s.user_id IS NOT NULL
        ORDER BY d.updated_at DESC
        """,
        (str(user_id), str(user_id), str(user_id)),
    )
    return [
        DocumentSummary(
            id=r["id"],
            title=r["title"],
            owner_id=r["owner_id"],
            access=r["access"],
            share_role=r["share_role"] if r["access"] == "shared" else None,
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.post("", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
def create_document(
    body: DocumentCreate,
    user_id: uuid.UUID = Depends(current_user_id),
) -> DocumentDetail:
    row = db.query(
        f"""
        INSERT INTO {DOC} (owner_id, title)
        VALUES (%s, %s)
        RETURNING id, title, owner_id, updated_at, initial_content, content_json
        """,
        (str(user_id), body.title or "Untitled"),
        one=True,
    )
    assert row
    acc = access.DocumentAccess(document_id=row["id"], role="owner")
    return _detail_from_row(row, acc, user_id)


@router.get("/users", response_model=list[UserListItem])
def list_users_for_sharing(user_id: uuid.UUID = Depends(current_user_id)) -> list[UserListItem]:
    rows = db.query(
        f"SELECT id, email, display_name FROM {U} WHERE id <> %s ORDER BY email",
        (str(user_id),),
    )
    return [UserListItem(id=r["id"], email=r["email"], display_name=r["display_name"]) for r in rows]


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID,
    user_id: uuid.UUID | None = Depends(optional_user_id),
    share_token: str | None = Query(None, description="Anyone-with-link token"),
) -> DocumentDetail:
    if user_id is None and not share_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in or pass share_token",
        )
    row = _fetch_doc_row(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, share_token)
    if acc is None:
        raise HTTPException(status_code=403, detail="No access")
    access.require(acc, "read")
    return _detail_from_row(row, acc, user_id)


@router.patch("/{document_id}", response_model=DocumentDetail)
def rename_document(
    document_id: uuid.UUID,
    body: DocumentRename,
    user_id: uuid.UUID = Depends(current_user_id),
) -> DocumentDetail:
    row = _fetch_doc_row(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    if acc is None:
        raise HTTPException(status_code=403, detail="No access")
    access.require(acc, "manage")
    db.query(
        f"""
        UPDATE {DOC} SET title = %s, updated_at = %s
        WHERE id = %s
        RETURNING id, title, owner_id, updated_at, initial_content, content_json
        """,
        (body.title, datetime.now(timezone.utc), str(document_id)),
        one=True,
    )
    row2 = _fetch_doc_row(document_id)
    assert row2
    return _detail_from_row(row2, acc, user_id)


@router.get("/{document_id}/content", response_model=DocumentContentOut)
def get_document_content(
    document_id: uuid.UUID,
    user_id: uuid.UUID | None = Depends(optional_user_id),
    share_token: str | None = Query(None),
) -> DocumentContentOut:
    if user_id is None and not share_token:
        raise HTTPException(status_code=401, detail="Sign in or pass share_token")
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, share_token)
    access.require(acc, "read")
    return _get_content_row(document_id)


@router.put("/{document_id}/content", response_model=DocumentContentOut)
def put_document_content(
    document_id: uuid.UUID,
    body: DocumentContentIn,
    user_id: uuid.UUID | None = Depends(optional_user_id),
    share_token: str | None = Query(None),
) -> DocumentContentOut:
    if user_id is None and not share_token:
        raise HTTPException(status_code=401, detail="Sign in or pass share_token")
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, share_token)
    access.require(acc, "write_content")
    return _save_content(document_id, body.content)


@router.post("/{document_id}/share", response_model=ShareOut)
def share_document(
    document_id: uuid.UUID,
    body: ShareIn,
    user_id: uuid.UUID = Depends(current_user_id),
) -> ShareOut:
    row = _fetch_doc_row(document_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    access.require(acc, "manage")
    target = db.query(
        f"SELECT id, email, display_name FROM {U} WHERE email = %s LIMIT 1",
        (str(body.email).lower(),),
        one=True,
    )
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if db.as_uuid(target["id"]) == user_id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    db.query(
        f"""
        INSERT INTO {SH} (document_id, user_id, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (document_id, user_id) DO UPDATE SET role = EXCLUDED.role
        """,
        (str(document_id), str(target["id"]), body.role),
    )
    return ShareOut(
        document_id=document_id,
        shared_with=UserOut(
            id=target["id"], email=target["email"], display_name=target["display_name"]
        ),
        role=body.role,
    )


@router.post("/{document_id}/share-link", response_model=ShareLinkOut)
def create_share_link(
    document_id: uuid.UUID,
    body: ShareLinkIn,
    user_id: uuid.UUID = Depends(current_user_id),
) -> ShareLinkOut:
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    access.require(acc, "manage")
    token = secrets.token_urlsafe(24)
    db.query(
        f"""
        UPDATE {DOC}
        SET share_token = %s, share_token_role = %s, updated_at = %s
        WHERE id = %s
        """,
        (token, body.role, datetime.now(timezone.utc), str(document_id)),
    )
    return ShareLinkOut(token=token, role=body.role)


@router.delete("/{document_id}/share-link")
def revoke_share_link(
    document_id: uuid.UUID,
    user_id: uuid.UUID = Depends(current_user_id),
):
    from starlette.responses import Response

    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    access.require(acc, "manage")
    db.query(
        f"""
        UPDATE {DOC} SET share_token = NULL, share_token_role = NULL, updated_at = %s
        WHERE id = %s
        """,
        (datetime.now(timezone.utc), str(document_id)),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/import/text", response_model=DocumentDetail, status_code=status.HTTP_201_CREATED)
async def import_text_document(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(current_user_id),
) -> DocumentDetail:
    name = file.filename or "import"
    suffix = ""
    if "." in name:
        suffix = "." + name.rsplit(".", 1)[-1].lower()
    if suffix not in _TEXT_IMPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Supported text imports: {', '.join(sorted(_TEXT_IMPORT))}",
        )
    data = await file.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text") from e
    title = name.rsplit(".", 1)[0] if "." in name else name
    row = db.query(
        f"""
        INSERT INTO {DOC} (owner_id, title, initial_content)
        VALUES (%s, %s, %s)
        RETURNING id, title, owner_id, updated_at, initial_content, content_json
        """,
        (str(user_id), title[:500], text),
        one=True,
    )
    assert row
    acc = access.DocumentAccess(document_id=row["id"], role="owner")
    return _detail_from_row(row, acc, user_id)


@router.post("/{document_id}/import-body", response_model=DocumentDetail)
async def import_text_into_existing_document(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(current_user_id),
) -> DocumentDetail:
    """Replace draft body from UTF-8 .txt / .md / .markdown; clears TipTap JSON so the editor seeds from text."""
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    if acc is None:
        raise HTTPException(status_code=403, detail="No access")
    access.require(acc, "write_content")

    name = file.filename or "import"
    suffix = ""
    if "." in name:
        suffix = "." + name.rsplit(".", 1)[-1].lower()
    if suffix not in _TEXT_IMPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Supported text imports: {', '.join(sorted(_TEXT_IMPORT))}",
        )
    data = await file.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text") from e

    row = db.query(
        f"""
        UPDATE {DOC}
        SET initial_content = %s, content_json = NULL, updated_at = %s
        WHERE id = %s
        RETURNING id, title, owner_id, updated_at, initial_content, content_json
        """,
        (text, datetime.now(timezone.utc), str(document_id)),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return _detail_from_row(row, acc, user_id)


@router.get("/{document_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(
    document_id: uuid.UUID,
    user_id: uuid.UUID | None = Depends(optional_user_id),
    share_token: str | None = Query(None),
) -> list[AttachmentOut]:
    if user_id is None and not share_token:
        raise HTTPException(status_code=401, detail="Sign in or pass share_token")
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, share_token)
    access.require(acc, "read")
    rows = db.query(
        f"""
        SELECT id, filename, content_type, byte_size, created_at
        FROM {ATT}
        WHERE document_id = %s
        ORDER BY created_at DESC
        """,
        (str(document_id),),
    )
    return [
        AttachmentOut(
            id=r["id"],
            filename=r["filename"],
            content_type=r["content_type"],
            byte_size=r["byte_size"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/{document_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(current_user_id),
) -> AttachmentOut:
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, None)
    access.require(acc, "write_content")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Max attachment size 5MB")
    fname = file.filename or "attachment"
    ctype = file.content_type or "application/octet-stream"
    row = db.query(
        f"""
        INSERT INTO {ATT} (document_id, filename, content_type, byte_size, data)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, filename, content_type, byte_size, created_at
        """,
        (str(document_id), fname[:255], ctype[:128], len(data), data),
        one=True,
    )
    assert row
    _touch_document(document_id)
    return AttachmentOut(
        id=row["id"],
        filename=row["filename"],
        content_type=row["content_type"],
        byte_size=row["byte_size"],
        created_at=row["created_at"],
    )


@router.get("/{document_id}/attachments/{attachment_id}/download")
def download_attachment(
    document_id: uuid.UUID,
    attachment_id: uuid.UUID,
    user_id: uuid.UUID | None = Depends(optional_user_id),
    share_token: str | None = Query(None),
):
    if user_id is None and not share_token:
        raise HTTPException(status_code=401, detail="Sign in or pass share_token")
    if not _fetch_doc_row(document_id):
        raise HTTPException(status_code=404, detail="Not found")
    acc = access.resolve_document_access(document_id, user_id, share_token)
    access.require(acc, "read")
    row = db.query(
        f"""
        SELECT filename, content_type, data
        FROM {ATT}
        WHERE id = %s AND document_id = %s
        LIMIT 1
        """,
        (str(attachment_id), str(document_id)),
        one=True,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    from fastapi.responses import Response

    return Response(
        content=bytes(row["data"]),
        media_type=row["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{row["filename"]}"'},
    )
