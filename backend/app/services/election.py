# app/services/election.py
# ─── Election Service ─────────────────────────────────────────────────────────
# Business logic layer. Routes call these functions, which call repositories.
# The key job here is serialization: converting ORM objects to the exact dict
# shapes the frontend JavaScript expects.
# ──────────────────────────────────────────────────────────────────────────────

import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.elections as repo
from app.schemas.election import ElectionCreateRequest, ElectionUpdateRequest


# ── Serializer ─────────────────────────────────────────────────────────────────

def serialize_election(election) -> dict:
    """
    Convert an Election ORM object (with loaded positions + candidates)
    into the exact dict shape the frontend expects.

    Frontend reads:
      el.id, el.title, el.shortName, el.category, el.status
      el.startDate, el.startTime, el.endDate, el.endTime, el.createdAt
      el.positions[i].title
      el.positions[i].candidates[j].name
      el.positions[i].candidates[j].emoji
      el.positions[i].candidates[j].info.{ role, score, manifesto, body, policies }
    """
    positions_out = []
    for pos in sorted(election.positions, key=lambda p: p.position_index):
        candidates_out = []
        for cand in sorted(pos.candidates, key=lambda c: c.candidate_index):
            candidates_out.append({
                "name":  cand.name,
                "emoji": cand.emoji or "👤",
                "info": {
                    "role":      cand.role            or "",
                    "score":     cand.score           or "N/A",
                    "manifesto": cand.manifesto_title or f"{cand.name}'s Manifesto",
                    "body":      cand.manifesto_body  or "",
                    "policies":  cand.policies        or [],
                }
            })
        positions_out.append({
            "title":      pos.title,
            "candidates": candidates_out,
        })

    return {
        "id":        election.id,
        "title":     election.title,
        "shortName": election.short_name  or election.title,
        "category":  election.category   or "",
        "status":    election.status,
        "startDate": election.start_date or "",
        "startTime": election.start_time or "08:00",
        "endDate":   election.end_date   or "",
        "endTime":   election.end_time   or "18:00",
        "createdAt": int(election.created_at.timestamp() * 1000) if election.created_at else 0,
        "positions": positions_out,
    }


# ── Service functions ──────────────────────────────────────────────────────────

def get_all_elections(db: Session) -> list[dict]:
    elections = repo.get_all_elections(db)
    return [serialize_election(e) for e in elections]


def get_election_by_id(db: Session, election_id: str) -> dict:
    election = repo.get_election_by_id(db, election_id)
    if not election:
        raise HTTPException(status_code=404, detail=f"Election '{election_id}' not found")
    return serialize_election(election)


def create_election(db: Session, payload: ElectionCreateRequest) -> dict:
    election_id = f"el_{uuid.uuid4().hex[:12]}"   # "el_a3f2b9c1d4e5"

    election_data = {
        "id":         election_id,
        "title":      payload.title,
        "short_name": payload.shortName or payload.title,
        "category":   payload.category,
        "status":     payload.status,
        "start_date": payload.startDate,
        "start_time": payload.startTime,
        "end_date":   payload.endDate,
        "end_time":   payload.endTime,
    }

    positions = [p.model_dump() for p in (payload.positions or [])]
    election  = repo.create_election(db, election_data, positions)
    return serialize_election(election)


def update_election(db: Session, election_id: str, payload: ElectionUpdateRequest) -> dict:
    election_data = {
        "title":      payload.title,
        "short_name": payload.shortName or payload.title,
        "category":   payload.category,
        "status":     payload.status,
        "start_date": payload.startDate,
        "start_time": payload.startTime,
        "end_date":   payload.endDate,
        "end_time":   payload.endTime,
    }

    positions = [p.model_dump() for p in (payload.positions or [])]
    election  = repo.update_election(db, election_id, election_data, positions)
    if not election:
        raise HTTPException(status_code=404, detail=f"Election '{election_id}' not found")
    return serialize_election(election)


def delete_election(db: Session, election_id: str):
    success = repo.delete_election(db, election_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Election '{election_id}' not found")