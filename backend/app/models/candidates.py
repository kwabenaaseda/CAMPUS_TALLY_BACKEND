# app/models/candidates.py
# ─── Candidate ────────────────────────────────────────────────────────────────
# A candidate belongs to one Position inside one Election.
# candidate_index (0-based) is the stable reference used by the Vote table —
# it matches the index of this candidate inside position.candidates[] on the
# frontend, so look-ups never need name matching.
#
# FIELDS CHANGED FROM ORIGINAL:
#   vetting_score: Integer  →  String ("87/100")  — matches frontend contract
#   Added: manifesto_title, manifesto_body, policies (JSON), role, emoji
#   Removed: vote_count  — votes are tallied live from the votes table
#   Added: position_id FK + position_index (denorm) for fast stats queries
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id              = Column(Integer, primary_key=True, index=True)
    election_id     = Column(String,  ForeignKey("elections.id",  ondelete="CASCADE"), nullable=False, index=True)
    position_id     = Column(Integer, ForeignKey("positions.id",  ondelete="CASCADE"), nullable=False, index=True)
    position_index  = Column(Integer, nullable=False)     # denorm: same as position.position_index
    candidate_index = Column(Integer, nullable=False)     # 0-based within the position

    name            = Column(String,  nullable=False)
    emoji           = Column(String,  default="👤")
    role            = Column(String)                      # "SRC Presidential Candidate"
    score           = Column(String)                      # "87/100" — string, not int
    manifesto_title = Column(String)                      # "A New Dawn for Students"
    manifesto_body  = Column(Text)                        # long description
    policies        = Column(JSON,    default=list)       # ["policy 1", "policy 2"]
    profile_picture = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ──────────────────────────────────────────────────────────
    position = relationship("Position", back_populates="candidates")