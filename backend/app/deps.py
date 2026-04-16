from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def current_user_id(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> uuid.UUID:
    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        return uuid.UUID(creds.credentials.strip())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


def optional_user_id(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> uuid.UUID | None:
    if creds is None or not creds.credentials:
        return None
    try:
        return uuid.UUID(creds.credentials.strip())
    except ValueError:
        return None
