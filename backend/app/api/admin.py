from fastapi import APIRouter, Depends, HTTPException, Depends
from sqlalchemy.orm import Session

import app.schemas.user as UL
import app.services.auth as auth_service
from app.db.deps import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ========= Routes with /api/admin prefix =========#
#=== Authentication and Authorization routes for Admin ===#

# Admin login Endpoint
@router.post("/login", response_model=UL.AdminAuthResponse)
async def admin_login(payload: UL.AdminLoginRequest, db: Session = Depends(get_db)):
    token = auth_service.login_admin(db,payload)
    return UL.AdminAuthResponse(
        token=token["token"]
    )

# Add new admin Endpoint
@router.post("/add")
def add_admin():
    # Implement logic to add new admin here
    return 

# Remove admin Endpoint
@router.delete("/remove")
def remove_admin():
    # Implement logic to remove admin here
    return {"message": "Admin removed successfully"} 

# ======= Other admin-specific routes can be added here =======#

# 