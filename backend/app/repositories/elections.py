# app/repositories/elections.py
# ─── Elections Repository ─────────────────────────────────────────────────────
# All DB reads and writes for elections, their positions, and their candidates.
# Services call these functions — routes never touch the DB directly.
# ──────────────────────────────────────────────────────────────────────────────

from sqlalchemy.orm import Session
from app.models.Election import Election
from app.models.position import Position
from app.models.candidates import Candidate


# ── Read ───────────────────────────────────────────────────────────────────────

def get_all_elections(db: Session):
    """Return all elections ordered newest-first."""
    return (
        db.query(Election)
        .order_by(Election.created_at.desc())
        .all()
    )


def get_election_by_id(db: Session, election_id: str):
    return db.query(Election).filter(Election.id == election_id).first()


def get_election_count(db: Session) -> int:
    return db.query(Election).count()


# ── Write ──────────────────────────────────────────────────────────────────────

def create_election(db: Session, election_data: dict, positions: list) -> Election:
    """
    Create an election with its full position + candidate tree in one transaction.

    election_data  — dict of Election column values (id, title, status, …)
    positions      — list of position dicts:
                     [{ "title": str, "candidates": [{ "name", "emoji", "info": {...} }] }]
    """
    election = Election(**election_data)
    db.add(election)
    db.flush()   # assign election.id before inserting children

    _insert_positions(db, str(election.id), positions)

    db.commit()
    db.refresh(election)
    return election


def update_election(db: Session, election_id: str, election_data: dict, positions: list):
    """
    Replace an election's basic fields + rebuild its entire position/candidate tree.
    Cascade delete on Position handles removing old candidates automatically.
    """
    election = get_election_by_id(db, election_id)
    if not election:
        return None

    for key, value in election_data.items():
        setattr(election, key, value)

    # Drop all existing positions (cascades to candidates via DB FK)
    db.query(Position).filter(Position.election_id == election_id).delete()
    db.flush()

    _insert_positions(db, str(election.id), positions)

    db.commit()
    db.refresh(election)
    return election


def delete_election(db: Session, election_id: str) -> bool:
    election = get_election_by_id(db, election_id)
    if not election:
        return False
    db.delete(election)
    db.commit()
    return True


# ── Internal helper ────────────────────────────────────────────────────────────

def _insert_positions(db: Session, election_id: str, positions: list):
    """Insert Position + Candidate rows for one election. Caller must flush/commit."""
    for pos_idx, pos_data in enumerate(positions):
        pos = Position(
            election_id    = election_id,
            position_index = pos_idx,
            title          = pos_data.get("title", f"Position {pos_idx + 1}")
        )
        db.add(pos)
        db.flush()   # get pos.id

        for cand_idx, cand_data in enumerate(pos_data.get("candidates", [])):
            info = cand_data.get("info", {})
            cand = Candidate(
                election_id     = election_id,
                position_id     = pos.id,
                position_index  = pos_idx,
                candidate_index = cand_idx,
                name            = cand_data.get("name", "Unknown"),
                emoji           = cand_data.get("emoji", "👤"),
                role            = info.get("role", ""),
                score           = info.get("score", "N/A"),
                manifesto_title = info.get("manifesto", ""),
                manifesto_body  = info.get("body", ""),
                policies        = info.get("policies", []),
            )
            db.add(cand)