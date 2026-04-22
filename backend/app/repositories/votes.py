# app/repositories/votes.py
# ─── Votes Repository ─────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models.vote import Vote


def cast_vote(db: Session, voter_id: int, election_id: str, position_index: int, candidate_index: int):
    """
    Insert one vote row.
    Returns (vote, error_message).
    If the unique constraint fires (voted twice for this position), returns (None, "already_voted").
    """
    vote = Vote(
        voter_id        = voter_id,
        election_id     = election_id,
        position_index  = position_index,
        candidate_index = candidate_index
    )
    db.add(vote)
    try:
        db.commit()
        db.refresh(vote)
        return vote, None
    except IntegrityError:
        db.rollback()
        return None, "already_voted"


def get_votes_by_voter(db: Session, voter_id: int):
    """All votes cast by a specific voter across all elections."""
    return (
        db.query(Vote)
        .filter(Vote.voter_id == voter_id)
        .order_by(Vote.created_at.desc())
        .all()
    )


def get_votes_by_election(db: Session, election_id: str):
    """All votes cast in a specific election (admin/stats use)."""
    return (
        db.query(Vote)
        .filter(Vote.election_id == election_id)
        .all()
    )


def get_vote_for_position(db: Session, voter_id: int, election_id: str, position_index: int):
    """Return the specific vote a voter cast for one position, or None."""
    return (
        db.query(Vote)
        .filter(
            Vote.voter_id       == voter_id,
            Vote.election_id    == election_id,
            Vote.position_index == position_index
        )
        .first()
    )


def has_voted_in_election(db: Session, voter_id: int, election_id: str) -> bool:
    """True if the voter has cast at least one vote in this election."""
    return (
        db.query(Vote)
        .filter(Vote.voter_id == voter_id, Vote.election_id == election_id)
        .first()
    ) is not None


def count_total_votes(db: Session) -> int:
    """Total vote rows across all elections."""
    return db.query(func.count(Vote.id)).scalar() or 0


def tally_position(db: Session, election_id: str, position_index: int):
    """
    Return vote counts grouped by candidate_index for one position.
    Result: [(candidate_index, vote_count), ...]
    """
    rows = (
        db.query(Vote.candidate_index, func.count(Vote.id).label("votes"))
        .filter(Vote.election_id == election_id, Vote.position_index == position_index)
        .group_by(Vote.candidate_index)
        .all()
    )
    return rows   # list of Row(candidate_index=int, votes=int)