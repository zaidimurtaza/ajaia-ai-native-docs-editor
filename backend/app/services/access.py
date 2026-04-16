from __future__ import annotations

import hmac
import uuid
from dataclasses import dataclass
from typing import Literal

from fastapi import HTTPException, status

from app import db

Need = Literal["read", "write_content", "manage"]

D = db.tbl("documents")
S = db.tbl("document_shares")


@dataclass(frozen=True)
class DocumentAccess:
    """Effective permission for one document."""

    document_id: uuid.UUID
    role: Literal["owner", "editor", "viewer"]


def _merge_roles(a: str | None, b: str | None) -> str | None:
    if a and b:
        return "editor" if "editor" in (a, b) else "viewer"
    return a or b


def resolve_document_access(
    document_id: uuid.UUID,
    user_id: uuid.UUID | None,
    share_token: str | None,
) -> DocumentAccess | None:
    doc = db.query(
        f"""
        SELECT id, owner_id, share_token, share_token_role
        FROM {D}
        WHERE id = %s
        LIMIT 1
        """,
        (str(document_id),),
        one=True,
    )
    if not doc:
        return None

    if user_id is not None and db.as_uuid(doc["owner_id"]) == user_id:
        return DocumentAccess(document_id=document_id, role="owner")

    shared_role: str | None = None
    if user_id is not None:
        row = db.query(
            f"""
            SELECT role FROM {S}
            WHERE document_id = %s AND user_id = %s
            LIMIT 1
            """,
            (str(document_id), str(user_id)),
            one=True,
        )
        if row:
            shared_role = row["role"]

    link_role: str | None = None
    st = doc["share_token"]
    if share_token and st and hmac.compare_digest(str(st), share_token):
        link_role = doc["share_token_role"]

    effective = _merge_roles(shared_role, link_role)
    if effective is None:
        return None
    if effective not in ("viewer", "editor"):
        return None
    return DocumentAccess(document_id=document_id, role=effective)  # type: ignore[arg-type]


def can_manage(access: DocumentAccess) -> bool:
    return access.role == "owner"


def can_edit_content(access: DocumentAccess) -> bool:
    return access.role in ("owner", "editor")


def require(access: DocumentAccess | None, need: Need) -> DocumentAccess:
    if access is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access")
    if need == "read":
        return access
    if need == "manage" and not can_manage(access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if need == "write_content" and not can_edit_content(access):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Read only")
    return access
