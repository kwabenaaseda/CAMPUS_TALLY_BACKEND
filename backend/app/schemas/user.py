# app/schemas/user.py
# ─── User / Auth Schemas ──────────────────────────────────────────────────────
# IMPORTANT: field names here must match what the frontend JavaScript sends.
#
# register.html → api_handler.registerUser({ name, id, index, course, password })
# index.html    → api_handler.loginUser(studentId, password)
#                   → POST body: { studentId, password }
# admin-login   → api_handler.adminLogin(adminId, password)
#                   → POST body: { adminId, password }
#
# The DB models use internal names (fullname, student_id, index_number, department).
# Services map from schema field names → DB field names.
# ──────────────────────────────────────────────────────────────────────────────

import re
from pydantic import BaseModel, field_validator
from typing import Optional


# ── Signup ────────────────────────────────────────────────────────────────────

class UserCreateRequest(BaseModel):
    name:     str    # → Voter.fullname
    id:       str    # → Voter.student_id  (the student types their ID)
    index:    str    # → Voter.index_number
    course:   str    # → Voter.department
    password: str

    @field_validator("name")
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Name should only contain letters and spaces")
        return v

    @field_validator("id", "index")
    def validate_ids(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("Must contain only letters and numbers")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not re.match(pattern, v):
            raise ValueError("Password must be 8+ chars with upper, lower, digit and special char")
        return v


# ── Login ─────────────────────────────────────────────────────────────────────

class UserLoginRequest(BaseModel):
    studentId: str   # matches api_handler: { studentId, password }
    password:  str


# ── Admin login ───────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    adminId:  str    # matches api_handler: { adminId, password }
    password: str


# ── Shared user dict (embedded in auth responses) ─────────────────────────────
# Matches the frontend's UserObject shape exactly.
# profile.html reads: user.id, user.name, user.course, user.index,
#                     user.level, user.votingStatus, user.createdAt

class UserOut(BaseModel):
    id:            str    # student_id
    name:          str    # fullname
    index:         str    # index_number
    course:        str    # department
    level:         str    # "400"
    votingStatus:  str    # "Verified"
    createdAt:     int    # Unix ms

    class Config:
        from_attributes = True


# ── Auth responses ────────────────────────────────────────────────────────────

class AuthResponse(BaseModel):
    token: str
    success: bool
    message: str
    user: dict


class AdminAuthResponse(BaseModel):
    token: str


# ── Admin management ──────────────────────────────────────────────────────────

class AdminCreateRequest(BaseModel):
    adminId:  str
    fullname: str
    password: str

    @field_validator("adminId")
    def validate_id(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("Admin ID must be alphanumeric")
        return v


class AdminRemoveRequest(BaseModel):
    adminId: str