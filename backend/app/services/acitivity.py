# app/services/activity.py
# ─── Activity Service ─────────────────────────────────────────────────────────

from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.activity as repo
import app.repositories.user as user_repo


def log_voted_activity(db: Session, student_id: str, payload) -> dict:
    """
    Called from POST /activity (confirmation.html fires this after all positions done).
    payload is ActivityLogRequest: { type, electionId, electionName, ref, timestamp }
    """
    voter = user_repo.get_user_by_student_id(db, student_id)
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")

    repo.log_activity(db, voter.id,  { # type: ignore
        "type":          payload.type,
        "election_id":   payload.electionId,
        "election_name": payload.electionName,
        "ref":           payload.ref,
        "timestamp":     payload.timestamp,
    })
    return {"ok": True}


def get_activity(db: Session, student_id: str) -> list[dict]:
    """
    GET /activity/:userId
    Returns the last 50 activity items, shaped for profile.html's render loop.
    Names are already pre-resolved on the Activity row so profile.html
    never needs to call getElectionById() per item.
    """
    voter = user_repo.get_user_by_student_id(db, student_id)
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")

    items = repo.get_activity_by_voter(db, voter.id)#type: ignore
    result = []
    for item in items:
        entry = {
            "type":          item.type,
            "electionId":    item.election_id,
            "electionName":  item.election_name,
            "timestamp":     item.timestamp,
        }
        if item.type == "vote":
            entry["positionIndex"]  = item.position_index
            entry["positionTitle"]  = item.position_title
            entry["candidateIndex"] = item.candidate_index
            entry["candidateName"]  = item.candidate_name
        elif item.type == "voted":
            entry["ref"] = item.ref
        result.append(entry)

    return result