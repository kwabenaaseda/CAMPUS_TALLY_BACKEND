from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.schemas.user as UL
import app.services.auth as auth_service
from app.db.deps import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/signup", response_model=UL.AuthResponse)
async def signup(payload: UL.UserCreateRequest, db: Session = Depends(get_db)):
    result = auth_service.signup_user(db, payload)

    token = result["token"]
    user_dict = result["user"]  # This is the dictionary from _serialize_user

    return UL.AuthResponse(
        token=token,
        success=True,
        message="User created successfully",
        user=user_dict  # Directly use the serialized user dictionary
)


@router.post("/login", response_model=UL.AuthResponse)
async def login(payload: UL.UserLoginRequest, db: Session = Depends(get_db)):
    inbound = auth_service.login_user(db, payload)
    token = inbound["token"]
    user = inbound["user"]

    return UL.AuthResponse(
        token=token,
        success=True,
        message="User logged in successfully",
        user=user  # This is already a dictionary from _serialize_user
    )

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models import Voter as User


# app/api/auth.py

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    # Map 'department' (DB) to 'course' (Frontend expectation)
    # Map 'student_id' (User) or 'id_code' (Admin) to 'id'
    return {
        "id": getattr(current_user, "student_id", getattr(current_user, "id_code", "N/A")),
        "name": getattr(current_user, "fullname", "User"),
        "course": getattr(current_user, "department", "N/A"), # FIXED: Maps department to course
        "index": getattr(current_user, "index_number", "N/A"),
        "level": getattr(current_user, "level", "N/A")
    }