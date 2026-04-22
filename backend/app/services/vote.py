# app/services/vote.py
# ─── Vote Service ─────────────────────────────────────────────────────────────

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.votes as vote_repo
import app.repositories.elections as election_repo
import app.repositories.user as user_repo
import app.repositories.activity as activity_repo


# ── Cast a vote ────────────────────────────────────────────────────────────────

def cast_vote(db: Session, student_id: str, election_id: str, position_index: int, candidate_index: int):
    """
    Validate then store one vote.
    Guards:
      - election must exist and be active
      - candidate_index must be valid for the position
      - voter must not have already voted for this position (409 if so)
    """
    # Validate election
    election = election_repo.get_election_by_id(db, election_id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    if election.status != "active":
        raise HTTPException(status_code=400, detail="Election is not currently active")

    # Validate position_index
    if position_index < 0 or position_index >= len(election.positions):
        raise HTTPException(status_code=400, detail="Invalid position index")

    # Validate candidate_index
    pos = election.positions[position_index]
    if candidate_index < 0 or candidate_index >= len(pos.candidates):
        raise HTTPException(status_code=400, detail="Invalid candidate index")

    # Resolve voter DB id from student_id
    voter = user_repo.get_user_by_student_id(db, student_id)
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")

    # Cast the vote
    vote, error = vote_repo.cast_vote(db, voter.id, election_id, position_index, candidate_index) # type: ignore
    if error == "already_voted":
        raise HTTPException(status_code=409, detail="You have already voted for this position")
    if not vote:
        raise HTTPException(status_code=500, detail="Failed to cast vote")
    
    # Log activity (position-level)
    cand = pos.candidates[candidate_index]
    activity_repo.log_activity(db, voter.id, { # type: ignore
        "type":            "vote",
        "election_id":     election_id,
        "election_name":   election.short_name or election.title,
        "position_index":  position_index,
        "position_title":  pos.title,
        "candidate_index": candidate_index,
        "candidate_name":  cand.name,
        "timestamp":       int(vote.created_at.timestamp() * 1000),
    })

    return {"ok": True, "message": f"Voted for {cand.name} successfully"}


# ── Get user votes ─────────────────────────────────────────────────────────────

def get_votes_by_voter(db: Session, student_id: str) -> list[dict]:
    """
    Return all votes cast by a voter as the VoteRecord list the frontend expects:
    [{ electionId, positionIndex, candidateIndex, timestamp }]
    """
    voter = user_repo.get_user_by_student_id(db, student_id)
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")

    votes = vote_repo.get_votes_by_voter(db, voter.id) # type: ignore
    return [
        {
            "electionId":     v.election_id,
            "positionIndex":  v.position_index,
            "candidateIndex": v.candidate_index,
            "timestamp":      int(v.created_at.timestamp() * 1000),
        }
        for v in votes
    ]


# ── Get election votes (admin) ─────────────────────────────────────────────────

def get_votes_by_election(db: Session, election_id: str) -> list[dict]:
    votes = vote_repo.get_votes_by_election(db, election_id)
    return [
        {
            "voterId":        v.voter_id,
            "positionIndex":  v.position_index,
            "candidateIndex": v.candidate_index,
            "timestamp":      int(v.created_at.timestamp() * 1000),
        }
        for v in votes
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# app/services/stats.py  (included in this file to avoid extra imports)
# ─── Stats Service ────────────────────────────────────────────────────────────

import app.repositories.votes as _vote_repo
import app.repositories.elections as _election_repo
from app.models.user import Voter


def get_election_stats(db: Session, election_id: str) -> dict:
    """
    Build the stats payload for one election.
    Expected by results.html and dashboard.html via tallyPosition().

    Response shape:
    {
      "electionId":  "src_2024",
      "totalVotes":  15200,
      "positions": [
        {
          "positionIndex": 0,
          "title":         "SRC President",
          "totalVotes":    5200,
          "candidates": [
            { "candidateIndex": 0, "votes": 2340, "pct": 45 },
            ...
          ]
        }
      ]
    }
    """
    election = _election_repo.get_election_by_id(db, election_id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")

    election_total = 0
    positions_stats = []

    for pos in sorted(election.positions, key=lambda p: p.position_index):
        # Aggregate votes for this position from the DB
        tally_rows = _vote_repo.tally_position(db, election_id, pos.position_index)
        tally_map  = {row.candidate_index: row.votes for row in tally_rows}

        pos_total  = sum(tally_map.values())
        election_total += pos_total

        candidates_stats = []
        for cand in sorted(pos.candidates, key=lambda c: c.candidate_index):
            votes = tally_map.get(cand.candidate_index, 0)
            pct   = round((votes / pos_total * 100)) if pos_total > 0 else 0
            candidates_stats.append({
                "candidateIndex": cand.candidate_index,
                "votes":          votes,
                "pct":            pct,
            })

        positions_stats.append({
            "positionIndex": pos.position_index,
            "title":         pos.title,
            "totalVotes":    pos_total,
            "candidates":    candidates_stats,
        })

    return {
        "electionId": election_id,
        "totalVotes": election_total,
        "positions":  positions_stats,
    }


def get_admin_overview(db: Session) -> dict:
    """Stats for the admin dashboard stat cards."""
    from app.models.Election import Election
    from app.models.vote import Vote as VoteModel

    total_elections = db.query(Election).count()
    total_votes     = _vote_repo.count_total_votes(db)
    registered      = db.query(Voter).count()

    return {
        "totalElections":     total_elections,
        "totalVotes":         total_votes,
        "registeredStudents": registered,
    }