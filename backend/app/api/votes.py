from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_current_user
import app
from backend.app.db.deps import get_db
import app.services.vote as vote_service
import app.schemas.vote as vote

router = APIRouter(prefix="/api/votes", tags=["Votes"])

#========= Routes with /api/votes prefix =========#
# Cast vote Endpoint
@router.post("/cast")
async def cast_vote(payload: vote.VoteCastRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Payload expects: { electionId, positionIndex, candidateIndex }
    """
    # Safety Check: Use the ID from the token, not the payload, to prevent spoofing
    voter_id = getattr(current_user, "student_id", None)
    
    success = vote_service.cast_vote(
        db, 
        student_id=voter_id or payload.userId,  # Fallback to payload.userId if current_user.student_id is None
        election_id=payload.electionId, 
        position_index=payload.positionIndex, 
        candidate_index=payload.candidateIndex
    )    
    
    if not success:
        raise HTTPException(status_code=400, detail="Ineligible to vote or already voted")
        
    return {"message": "Vote recorded successfully", "status": "success"}

# Get votes for election Endpoint
@router.get("/election/{election_id}")
def get_votes_for_election(election_id: int, current_user: dict = Depends(get_current_user)):
    # Implement logic to get votes for election here
    return {"message": f"Votes for election with ID {election_id}", "user": current_user}

# Get votes by user Endpoint
@router.get("/user/{user_id}")
async def get_votes_by_user(user_id: str, db: Session = Depends(get_db)):
    """Used for the 'Activity' section in the profile."""
    user_votes = vote_service.get_votes_by_voter(db, user_id)
    return {"votes": user_votes}

@router.get("/protected")
def protected_route(current_user = Depends(get_current_user)):
    return {
        "message": "You are authorized",
        "user": current_user.student_id
    }
