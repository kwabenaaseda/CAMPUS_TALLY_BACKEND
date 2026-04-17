# app/core/deps.py

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import app.core.security as security
import app.repositories.user as repo
from app.db.deps import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = security.decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    role = payload.get("role")
    if not role:
        raise HTTPException(status_code=401, detail="Invalid token")
    if role == "admin":
        admin_id = payload.get("sub")

        if not admin_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = repo.get_admin_by_admin_id(db,admin_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    else:
        student_id = payload.get("sub")

        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = repo.get_user_by_student_id(db, student_id)

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user