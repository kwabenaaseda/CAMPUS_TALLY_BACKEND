from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import app.core.deps as MW
import app.services.election as election_service
import app.schemas.election as EL
from app.db.deps import get_db

router = APIRouter(prefix="/api/elections", tags=["election"])

#========= Routes with /api/elections prefix =========#
# Create election Endpoint
@router.post("/create")
def create_election():
    # Implement election creation logic here
    return {"message": "Election created successfully"}

# Get all elections Endpoint
@router.get("/all")
async def get_all_elections(
    db: Session = Depends(get_db),
):
    # Implement logic to get all elections here
   
    Elections = election_service.get_all_elections(db)
    return {"message": "List of all elections","elections":Elections}

# Get election by ID Endpoint
@router.get("/{election_id}")
def get_election_by_id(election_id: int):
    # Implement logic to get election by ID here
    return {"message": f"Details of election with ID {election_id}"}

# Update election Endpoint
@router.put("/update/{election_id}")
def update_election(election_id: int):
    # Implement election update logic here
    return {"message": f"Election with ID {election_id} updated successfully"}

# Delete election Endpoint
@router.delete("/delete/{election_id}")
def delete_election(election_id: int):
    # Implement election deletion logic here
    return {"message": f"Election with ID {election_id} deleted successfully"}

