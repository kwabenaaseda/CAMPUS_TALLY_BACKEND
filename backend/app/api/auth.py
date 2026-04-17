from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.schemas.user as UL
import app.services.auth as auth_service
from app.db.deps import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/signup", response_model=UL.UserCreateResponse)
async def signup(payload: UL.UserCreateRequest, db: Session = Depends(get_db)):
    user, token = auth_service.signup_user(db, payload)

    return UL.UserCreateResponse(
        token=token,
        success=True,
        message="User created successfully",
        data={
            "fullname": user.fullname,
            "student_id": user.student_id,
            "index_number": user.index_number,
            "department": user.department
        }
    )


@router.post("/login", response_model=UL.UserLoginResponse)
async def login(payload: UL.UserLoginRequest, db: Session = Depends(get_db)):
    user, token = auth_service.login_user(db, payload)

    return UL.UserLoginResponse(
        token=token,
        success=True,
        message="User logged in successfully",
        data={
            "fullname": user.fullname,
            "student_id": user.student_id,
            "index_number": user.index_number,
            "department": user.department
        }
    )