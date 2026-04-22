# app/models/Election.py
# ─── Election ─────────────────────────────────────────────────────────────────
# CHANGES FROM ORIGINAL:
#   start_date, start_time, end_date, end_time: DateTime/Time → String
#     Reason: frontend sends "2024-10-20" and "08:00" string literals.
#     Storing as strings avoids parsing round-trips and format mismatches.
#   Added: relationships to Position (cascade delete)
#   Removed: vote_count, status_flag (status column alone is enough)
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Election(Base):
    __tablename__ = "elections"

    id         = Column(String, primary_key=True, index=True)
    title      = Column(String, nullable=False)
    short_name = Column(String)
    category   = Column(String)
    status     = Column(String, default="draft")   # draft | upcoming | active | closed

    # Stored as strings to match frontend format ("2024-10-20", "08:00")
    start_date = Column(String)
    start_time = Column(String)
    end_date   = Column(String)
    end_time   = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ──────────────────────────────────────────────────────────
    # Deleting an election cascades to positions → candidates automatically.
    positions = relationship(
        "Position",
        back_populates="election",
        order_by="Position.position_index",
        cascade="all, delete-orphan"
    )