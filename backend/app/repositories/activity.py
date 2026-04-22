# app/repositories/activity.py
# ─── Activity Repository ──────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.models.activity import Activity


def log_activity(db: Session, voter_id: int, payload: dict):
    """
    Insert one activity row. Caller passes a dict matching Activity columns.
    Expected keys differ by type:
      "voted": election_id, election_name, ref, timestamp
      "vote":  election_id, position_index, position_title,
               candidate_index, candidate_name, timestamp
    """
    activity = Activity(voter_id=voter_id, **payload)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activity_by_voter(db: Session, voter_id: int, limit: int = 50):
    """Return the last `limit` activity items for a voter, newest-first."""
    return (
        db.query(Activity)
        .filter(Activity.voter_id == voter_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .all()
    )