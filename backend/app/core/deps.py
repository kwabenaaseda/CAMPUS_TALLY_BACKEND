# app/core/deps.py
# ─── FastAPI Dependencies ─────────────────────────────────────────────────────
# Reusable Depends() callables for route protection.
#
# get_current_user  → any valid token (user or admin)
# get_current_voter → user token only (raises 403 for admin tokens)
# get_current_admin → admin token only (raises 403 for user tokens)
# ──────────────────────────────────────────────────────────────────────────────

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import app.core.security as security
import app.repositories.user as repo
import app.repositories.admin as admin_repo
from app.db.deps import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
):
    """Accepts any valid token and returns the appropriate user/admin object."""
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    role = payload.get("role")
    sub  = payload.get("sub")

    if not role or not sub:
        raise HTTPException(status_code=401, detail="Malformed token")

    if role == "admin":
        user = admin_repo.get_admin_by_id_code(db, sub)
        if not user:
            raise HTTPException(status_code=401, detail="Admin not found")
        return user
    else:
        user = repo.get_user_by_student_id(db, sub)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user


def get_current_voter(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
):
    """Voter-only dependency. Admins get 403."""
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("role") != "user":
        raise HTTPException(status_code=403, detail="Voter access required")

    student_id = payload.get("sub")
    user = repo.get_user_by_student_id(db, str(student_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
):
    """Admin-only dependency. Regular users get 403."""
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    admin_id = payload.get("sub")
    admin = admin_repo.get_admin_by_id_code(db, str(admin_id))
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin