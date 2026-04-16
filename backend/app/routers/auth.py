from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app import db
from app.schemas import LoginIn, LoginOut, UserOut
from app.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

U = db.tbl("users")


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn) -> LoginOut:
    row = db.query(
        f"""
        SELECT id, email, display_name, password
        FROM {U}
        WHERE email = %s
        LIMIT 1
        """,
        (str(body.email).lower(),),
        one=True,
    )
    if not row or not verify_password(body.password, row["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    uid = row["id"]
    return LoginOut(
        access_token=str(uid),
        user=UserOut(id=uid, email=row["email"], display_name=row["display_name"]),
    )
