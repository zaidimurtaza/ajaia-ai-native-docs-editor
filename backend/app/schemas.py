from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    owner_id: uuid.UUID
    access: str  # owner | shared
    share_role: str | None = None  # viewer | editor when shared
    updated_at: datetime


class DocumentDetail(BaseModel):
    id: uuid.UUID
    title: str
    owner_id: uuid.UUID
    access: str  # owner | shared | link
    role: Literal["owner", "editor", "viewer"]
    updated_at: datetime
    initial_content: str | None
    has_content: bool


class DocumentCreate(BaseModel):
    title: str | None = Field(default="Untitled", max_length=500)


class DocumentRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class DocumentContentOut(BaseModel):
    content: dict[str, Any] | None


class DocumentContentIn(BaseModel):
    content: dict[str, Any]


class ShareIn(BaseModel):
    email: EmailStr
    role: Literal["viewer", "editor"] = "editor"


class ShareOut(BaseModel):
    document_id: uuid.UUID
    shared_with: UserOut
    role: Literal["viewer", "editor"]


class ShareLinkIn(BaseModel):
    role: Literal["viewer", "editor"] = "viewer"


class ShareLinkOut(BaseModel):
    token: str
    role: Literal["viewer", "editor"]


class UserListItem(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    byte_size: int
    created_at: datetime
