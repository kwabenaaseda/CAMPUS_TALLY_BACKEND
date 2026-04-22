# app/models/position.py
# ─── Position ─────────────────────────────────────────────────────────────────
# One election has many positions (SRC President, VP, General Secretary…).
# Positions are ordered by position_index (0-based) which matches the frontend
# positions[] array index exactly — no mapping needed.
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Position(Base):
    __tablename__ = "positions"

    id             = Column(Integer, primary_key=True, index=True)
    election_id    = Column(String, ForeignKey("elections.id", ondelete="CASCADE"), nullable=False, index=True)
    position_index = Column(Integer, nullable=False)   # 0-based, matches frontend array order
    title          = Column(String,  nullable=False)   # "SRC President"

    created_at = Column(DateTime, default=datetime.utcnow)

    # ── Relationships ──────────────────────────────────────────────────────────
    election   = relationship("Election",   back_populates="positions")
    candidates = relationship(
        "Candidate",
        back_populates="position",
        order_by="Candidate.candidate_index",
        cascade="all, delete-orphan"
    )