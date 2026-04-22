# app/services/auth.py
# ─── Auth Service ─────────────────────────────────────────────────────────────
# BUGS FIXED FROM ORIGINAL:
#
# 1. login_admin: subject={"id": admin.id_code} was a DICT.
#    create_access_token does str(subject) → "{'id': 'admin'}" (a dict repr string).
#    get_current_user then called get_admin_by_admin_id(db, "{'id': 'admin'}")
#    which returned None → every admin request returned 401.
#    FIX: subject=admin.id_code  (pass the string directly)
#
# 2. Field name mapping: UserCreateRequest now sends { name, id, index, course }
#    instead of { fullname, student_id, index_number, department }.
#    Service maps them to DB column names here.
# ──────────────────────────────────────────────────────────────────────────────

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.user as repo
import app.repositories.admin as admin_repo
import app.core.security as security

def get_val(obj, key, default=None):
    """Safely get value from either a Dict or an ORM Object."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_user(user) -> dict:
    return {
        "id":           get_val(user, "student_id"),
        "name":         get_val(user, "fullname"),
        "index":        get_val(user, "index_number"),
        "course":       get_val(user, "department"),
        "level":        str(get_val(user, "level", "400")),
        "votingStatus": "Verified",
        "createdAt":    int(user.created_at.timestamp() * 1000) if hasattr(user, 'created_at') and user.created_at else 0,
    }


# ── User auth ─────────────────────────────────────────────────────────────────

def signup_user(db: Session, payload):
    """payload is a UserCreateRequest with fields: name, id, index, course, password"""
    existing = repo.get_user_by_student_id(db, payload.id)
    if existing:
        raise HTTPException(status_code=400, detail="Student ID already registered")

    user_data = {
        "fullname":        payload.name,
        "student_id":      payload.id,
        "index_number":    payload.index,
        "department":      payload.course,
        "hashed_password": security.get_password_hash(payload.password),
    }

    new_user = repo.create_user(db, user_data)
    token    = security.create_access_token(subject=new_user.student_id, role="user")

    return {"token": token, "user": _serialize_user(new_user)}



def login_user(db: Session, payload):
    user = repo.get_user_by_student_id(db, payload.studentId)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Safe extraction
    db_pass = get_val(user, "hashed_password")
    user_id = get_val(user, "student_id")

    if not security.verify_password(payload.password, str(db_pass)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = security.create_access_token(subject=user_id, role="user")
    return {"token": token, "user": _serialize_user(user)}



# ── Admin auth ─────────────────────────────────────────────────────────────────

def login_admin(db: Session, payload):
    admin = admin_repo.get_admin_by_id_code(db, payload.adminId)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db_pass = get_val(admin, "hashed_password")
    admin_id = get_val(admin, "id_code")

    if not security.verify_password(payload.password, str(db_pass)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = security.create_access_token(subject=admin_id, role="admin")
    return {"token": token, "admin": {"id": admin_id}}