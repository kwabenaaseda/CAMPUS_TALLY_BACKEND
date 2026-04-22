from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Vote

def get_election_stats(db: Session, election_id: str):
    """Returns vote counts grouped by candidate_id for a given election."""
    return db.query(
        Vote.candidate_index.label("candidate_id"), 
        func.count(Vote.id).label("total_votes")
    ).filter(Vote.election_id == election_id).group_by(Vote.candidate_index).all()