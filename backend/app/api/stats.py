from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.services import stats as stats_service

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("/election/{election_id}")
async def get_election_results(election_id: str, db: Session = Depends(get_db)):
    """
    FIX: election_id is now 'str' to accept 'dept_2023' etc.
    This resolves the 422 Unprocessable Entity errors.
    """
    stats = stats_service.get_formatted_stats(db, election_id)
    return {
        "election_id": election_id,
        "results": stats
    }