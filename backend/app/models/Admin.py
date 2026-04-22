import uuid

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.db.database import Base


class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, index=True)
    id_code = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))  # Unique ID code for admin login
    fullname = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_root = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

