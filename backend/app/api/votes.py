from fastapi import APIRouter, Depends, HTTPException, Depends
from app.core.deps import get_current_user


router = APIRouter(prefix="/api/votes", tags=["Votes"])

#========= Routes with /api/votes prefix =========#
# Cast vote Endpoint
@router.post("/cast")
def cast_vote(current_user: dict = Depends(get_current_user)):
    # Implement vote casting logic here
    return {"message": "Vote cast successfully", "user": current_user}

# Get votes for election Endpoint
@router.get("/election/{election_id}")
def get_votes_for_election(election_id: int, current_user: dict = Depends(get_current_user)):
    # Implement logic to get votes for election here
    return {"message": f"Votes for election with ID {election_id}", "user": current_user}

# Get votes by user Endpoint
@router.get("/user/{user_id}")
def get_votes_by_user(user_id: int):
    # Implement logic to get votes by user here
    return {"message": f"Votes cast by user with ID {user_id}"}


@router.get("/protected")
def protected_route(current_user = Depends(get_current_user)):
    return {
        "message": "You are authorized",
        "user": current_user.student_id
    }
