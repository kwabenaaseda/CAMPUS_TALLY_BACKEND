# app/schemas/election.py
# ─── Election Schemas ──────────────────────────────────────────────────────────
# These are the exact shapes the frontend sends (create-election.html admin form)
# and receives (dashboard.html, elections.html, voting.html, results.html).
# Field names match the frontend JavaScript object keys precisely.
# ──────────────────────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional


# ── Inbound: Create / Update ───────────────────────────────────────────────────

class CandidateInfoIn(BaseModel):
    role:      str = ""
    score:     str = "N/A"
    manifesto: str = ""        # manifesto title / headline
    body:      str = ""        # long manifesto body
    policies:  list[str] = []


class CandidateIn(BaseModel):
    name:  str
    emoji: str = "👤"
    info:  CandidateInfoIn = CandidateInfoIn()


class PositionIn(BaseModel):
    title:      str
    candidates: list[CandidateIn] = []


class ElectionCreateRequest(BaseModel):
    """Body for POST /elections/create and PUT /elections/update/:id"""
    title:     str
    shortName: str = ""
    category:  str
    status:    str = "draft"   # draft | upcoming | active | closed
    startDate: str
    startTime: str = "08:00"
    endDate:   str
    endTime:   str = "18:00"
    positions: list[PositionIn] = []


# ── Outbound: Response shapes ──────────────────────────────────────────────────
# These match the frontend's ElectionObject, CandidateObject, PositionObject.

class CandidateInfoOut(BaseModel):
    role:      str
    score:     str
    manifesto: str   # title
    body:      str
    policies:  list[str]

class CandidateOut(BaseModel):
    name:  str
    emoji: str
    info:  CandidateInfoOut

class PositionOut(BaseModel):
    title:      str
    candidates: list[CandidateOut]

class ElectionOut(BaseModel):
    id:        str
    title:     str
    shortName: str
    category:  str
    status:    str
    startDate: str
    startTime: str
    endDate:   str
    endTime:   str
    createdAt: int             # Unix ms — matches frontend's el.createdAt
    positions: list[PositionOut]

    class Config:
        from_attributes = True


class ElectionListResponse(BaseModel):
    elections: list[ElectionOut]

class ElectionSingleResponse(BaseModel):
    election: ElectionOut

class ElectionResponse(BaseModel):
    message: str
    election: ElectionOut

class ElectionUpdateRequest(BaseModel):
    title:     Optional[str]
    shortName: Optional[str]
    category:  Optional[str]
    status:    Optional[str]   # draft | upcoming | active | closed
    startDate: Optional[str]
    startTime: Optional[str]
    endDate:   Optional[str]
    endTime:   Optional[str]
    positions: Optional[list[PositionIn]]

