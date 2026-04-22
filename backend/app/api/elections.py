from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.core.deps as MW
import app.services.election as election_service
import app.schemas.election as EL
from app.db.deps import get_db

router = APIRouter(prefix="/api/elections", tags=["election"])

#========= Routes with /api/elections prefix =========#
# Create election Endpoint
@router.post("/create", status_code=201)
async def create_election(payload: EL.ElectionCreateRequest, db: Session = Depends(get_db)):
    # Only admins should do this (add your admin dependency here later)
    return election_service.create_election(db, payload)

# Get all elections Endpoint
@router.get("/all")
async def get_all_elections(
    db: Session = Depends(get_db),
):
    # Implement logic to get all elections here
   
    Elections = election_service.get_all_elections(db)
    return {"message": "List of all elections","elections":Elections}

# Get election by ID Endpoint
@router.get("/{election_id}", response_model=EL.ElectionSingleResponse)
async def get_election(election_id: str, db: Session = Depends(get_db)):
    election = election_service.get_election_by_id(db, election_id)
    if not election:
        raise HTTPException(status_code=404, detail="Election not found")
    return election

# Update election Endpoint
@router.put("/update/{election_id}")
async def update_election(election_id: str, payload: EL.ElectionUpdateRequest, db: Session = Depends(get_db)):
    # Implement election update logic here
    updated_election = election_service.update_election(db, election_id, payload)
    if not updated_election:
        raise HTTPException(status_code=404, detail="Election not found")
    return {"message": f"Election with ID {election_id} updated successfully", "election": updated_election}

# Delete election Endpoint
@router.delete("/delete/{election_id}")
async def delete_election(election_id: str, db: Session = Depends(get_db)):
    # Implement election deletion logic here
    deleted = election_service.delete_election(db, election_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Election not found")
    return {"message": f"Election with ID {election_id} deleted successfully"}

