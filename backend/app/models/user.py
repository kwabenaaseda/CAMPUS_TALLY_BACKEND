from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.database import Base

class Voter(Base):
    __tablename__ = "voters"

    id = Column(Integer, primary_key=True, index=True)
    profile_picture = Column(Text)
    fullname = Column(String, index=True, nullable=False)
    student_id = Column(String, unique=True, index=True, nullable=False)
    index_number = Column(String, unique=True, index=True, nullable=False)
    level =  Column(Integer, nullable=False)
    department = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    # metadata 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

