# app/models/vote.py
# ─── Vote ─────────────────────────────────────────────────────────────────────
# One Vote row = one voter's choice for ONE POSITION in ONE ELECTION.
# A voter casts one Vote per position (not per election) which is why the
# unique constraint is on (voter_id, election_id, position_index).
#
# CHANGED FROM ORIGINAL:
#   Removed:  has_voted (bool) — useless, you can just check if a row exists
#   Added:    position_index   — which position in the election
#   Added:    candidate_index  — which candidate they chose (0-based)
#   Fixed:    UniqueConstraint declaration (was inside the class body wrong)
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.db.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id              = Column(Integer, primary_key=True, index=True)
    voter_id        = Column(Integer, ForeignKey("voters.id"),    nullable=False, index=True)
    election_id     = Column(String,  ForeignKey("elections.id"), nullable=False, index=True)
    position_index  = Column(Integer, nullable=False)   # which position
    candidate_index = Column(Integer, nullable=False)   # which candidate they chose

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # ── Constraints ───────────────────────────────────────────────────────────
    # A voter may only vote once per position per election.
    # Attempting a second vote returns 409 Conflict — not a 500.
    __table_args__ = (
        UniqueConstraint(
            "voter_id", "election_id", "position_index",
            name="uq_voter_election_position"
        ),
    )