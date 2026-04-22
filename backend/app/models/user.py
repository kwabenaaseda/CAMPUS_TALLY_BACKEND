# app/models/user.py
# ─── Voter ────────────────────────────────────────────────────────────────────
# CHANGE FROM ORIGINAL:
#   level: nullable=False  →  nullable=True, default=400
#   Reason: the signup form does not collect level, so every registration
#   would crash with an IntegrityError. Default 400 mirrors the app.js seed.
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.database import Base


class Voter(Base):
    __tablename__ = "voters"

    id              = Column(Integer, primary_key=True, index=True)
    profile_picture = Column(Text)
    fullname        = Column(String, index=True,  nullable=False)
    student_id      = Column(String, unique=True, nullable=False, index=True)
    index_number    = Column(String, unique=True, nullable=False, index=True)
    level           = Column(Integer, nullable=True, default=400)   # fixed: was NOT NULL with no default
    department      = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)