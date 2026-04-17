from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from app.db.database import Base
from uuid import uuid4, UUID

class Candidates(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True , index=True)
    election_id = Column(Integer ,
        ForeignKey(
        "elections.id"
    ))
    profile_picture = Column(Text)
    fullname = Column(String)
    index_number = Column(String)
    vetting_score = Column(Integer)
    manifesto_sum = Column(Text)
    #metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)