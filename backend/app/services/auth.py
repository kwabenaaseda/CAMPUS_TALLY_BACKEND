# app/services/auth.py

from fastapi import HTTPException
import app.repositories.user as repo
import app.core.security as security
import app.repositories.admin as admin_repo


def signup_user(db, payload):
    # Check if user exists
    existing_user = repo.get_user_by_student_id(db, payload.student_id)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash password
    hashed_password = security.get_password_hash(payload.password)

    # Prepare data
    user_data = {
        "fullname": payload.fullname,
        "student_id": payload.student_id,
        "index_number": payload.index_number,
        "department": payload.department,
        "hashed_password": hashed_password
    }

    # Save user
    new_user = repo.create_user(db, user_data)

    # Generate token
    token = security.create_access_token(subject=new_user.student_id,role="user")

    return new_user, token


def login_user(db, payload):
    user = repo.get_user_by_student_id(db, payload.student_id)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not security.verify_password(payload.password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = security.create_access_token(subject=user.student_id,role="user")

    return user, token


def login_admin(db, payload):
    admin = admin_repo.get_admin_by_id_code(db, payload.id_code)

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not security.verify_password(payload.password, str(admin.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 🔥 Important: differentiate token identity
    token = security.create_access_token(
        subject={"id": admin.id_code},
        role="admin"
    )

    return admin, token