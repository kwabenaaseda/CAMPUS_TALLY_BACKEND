from pydantic import BaseModel
from typing import Optional

# Signup
# app/schemas/user.py

from pydantic import BaseModel, field_validator
import re

class UserCreateRequest(BaseModel):
    fullname: str
    student_id: str
    index_number: str
    department: str
    password: str

    @field_validator("fullname")
    def validate_fullname(cls, v):
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Fullname should only contain letters and spaces")
        return v

    @field_validator("student_id", "index_number")
    def validate_ids(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("Must contain only letters and numbers")
        return v

    @field_validator("department")
    def validate_department(cls, v):
        if not re.match(r"^[a-zA-Z\s]+$", v):
            raise ValueError("Department invalid")
        return v

    @field_validator("password")
    def validate_password(cls, v):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not re.match(pattern, v):
            raise ValueError("Weak password")
        return v

class UserCreateResponse(BaseModel):
    token: str
    success: bool
    message: str
    data: Optional[dict]
    

class UserCreateError(BaseModel):
    detail: str
    success: bool


# Login
class UserLoginRequest(BaseModel):
    student_id: str
    password: str

    @field_validator("student_id")
    def validate_student_id(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("Student ID should only contain letters and numbers")
        return v
    
    @field_validator("password")
    def validate_password(cls, v):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not re.match(pattern, v):
            raise ValueError("Weak password")
        return v

class UserLoginResponse(BaseModel):
    token: str
    success: bool
    message: str
    data: Optional[dict]

class UserLoginError(BaseModel):
    detail: str
    success: bool

# Update user
class UserUpdate(BaseModel):
    token: str
    profile_picture: Optional[str]
    fullname:Optional[str]
    student_id:Optional[str]
    index_number:Optional[str]
    department:Optional[str]
    level:Optional[int]

class UpdatePassword(BaseModel):
    password: str
    token: str



# Get User Data 
class GetUserDataResponse(BaseModel):
    token: str
    profile_picture: Optional[str]
    fullname:str
    student_id:str
    index_number:str
    department:str
    level:Optional[int]








# Admin Login
class AdminLogin(BaseModel):
    id_code: str
    password: str

    @field_validator("id_code")
    def validate_id_code(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("adminId should only contain letters and numbers")
        return v
    
    @field_validator("password")
    def validate_password(cls, v):
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not re.match(pattern, v):
            raise ValueError("Weak password")
        return v


class AdminLoginResponse(BaseModel):
    token: str
    success: bool
    message: str
    data: Optional[dict]    

class AdminLoginResponseError(BaseModel):
    detail: str