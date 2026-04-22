# app/schemas/vote.py
# ─── Vote Schemas ─────────────────────────────────────────────────────────────

from pydantic import BaseModel


class VoteCastRequest(BaseModel):
    """Body for POST /votes/cast — field names match api_handler.js castVote()."""
    userId:         str     # student_id of the voter
    electionId:     str
    positionIndex:  int
    candidateIndex: int


class VoteRecord(BaseModel):
    """One vote entry in GET /votes/user/:userId response."""
    electionId:     str
    positionIndex:  int
    candidateIndex: int
    timestamp:      int     # Unix ms


class VoteListResponse(BaseModel):
    votes: list[VoteRecord]


class VoteCastResponse(BaseModel):
    ok:      bool
    message: str


# ─── Stats Schemas ────────────────────────────────────────────────────────────

class CandidateStats(BaseModel):
    candidateIndex: int
    votes:          int
    pct:            int     # pre-computed percentage (0-100)


class PositionStats(BaseModel):
    positionIndex: int
    title:         str
    totalVotes:    int
    candidates:    list[CandidateStats]


class ElectionStatsResponse(BaseModel):
    electionId:  str
    totalVotes:  int
    positions:   list[PositionStats]


class AdminOverviewResponse(BaseModel):
    totalElections:      int
    totalVotes:          int
    registeredStudents:  int


# ─── Activity Schemas ─────────────────────────────────────────────────────────

class ActivityLogRequest(BaseModel):
    """Body for POST /activity — fired by confirmation.html."""
    type:          str               # "voted"
    electionId:    str
    electionName:  str
    ref:           str               # "CT-2024-5432"
    timestamp:     int               # Unix ms


class ActivityItem(BaseModel):
    type:           str
    electionId:     str | None
    electionName:   str | None
    timestamp:      int
    # "vote" fields
    positionIndex:  int | None       = None
    positionTitle:  str | None       = None
    candidateIndex: int | None       = None
    candidateName:  str | None       = None
    # "voted" fields
    ref:            str | None       = None


class ActivityListResponse(BaseModel):
    activity: list[ActivityItem]