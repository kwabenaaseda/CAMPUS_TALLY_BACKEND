# app/models/activity.py
# ─── Activity ─────────────────────────────────────────────────────────────────
# Stores a chronological log of voter actions.
# Two event types produced by the frontend:
#
#   "vote"  — fired by castVote() after each individual position vote
#             carries: election_id, position_index, candidate_index
#             + pre-resolved names so profile.html doesn't need extra calls
#
#   "voted" — fired by confirmation.html after all positions complete
#             carries: election_id, election_name, ref (CT-2024-XXXX)
#
# profile.html reads this directly and renders it without further queries.
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, BigInteger, DateTime, ForeignKey
from datetime import datetime
from app.db.database import Base


class Activity(Base):
    __tablename__ = "activity"

    id              = Column(Integer, primary_key=True, index=True)
    voter_id        = Column(Integer, ForeignKey("voters.id"), nullable=False, index=True)
    type            = Column(String,  nullable=False)    # "voted" | "vote"

    # Shared fields
    election_id     = Column(String,  nullable=True)
    election_name   = Column(String,  nullable=True)
    timestamp       = Column(BigInteger, nullable=False) # Unix milliseconds (from frontend)

    # For type="vote" only
    position_index  = Column(Integer, nullable=True)
    position_title  = Column(String,  nullable=True)    # pre-resolved
    candidate_index = Column(Integer, nullable=True)
    candidate_name  = Column(String,  nullable=True)    # pre-resolved

    # For type="voted" only
    ref             = Column(String,  nullable=True)    # "CT-2024-5432"

    created_at = Column(DateTime, default=datetime.utcnow)