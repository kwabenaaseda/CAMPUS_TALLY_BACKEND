# app/repositories/admin.py

from sqlalchemy.orm import Session
import app.models.Admin as AM

def get_admin_by_id_code(db: Session, id_code: str):
    return db.query(AM.Admin).filter(AM.Admin.id_code == id_code).first()