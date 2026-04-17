from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from app.db.database import Base

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    election_id = Column(Integer, ForeignKey(
        "elections.id"
    ), index=True)
    voter_id = Column(Integer ,ForeignKey("voters.id"), index=True)
    has_voted = Column(Boolean, default=False, index=True)
    # metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)