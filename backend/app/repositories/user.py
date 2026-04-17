# app/repositories/user.py

from sqlalchemy.orm import Session
import app.models.user as UM
import app.models.Admin as UA

def get_user_by_student_id(db: Session, student_id: str):
    return db.query(UM.Voter).filter(UM.Voter.student_id == student_id).first()

def create_user(db: Session, user_data: dict):
    user = UM.Voter(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_admin_by_admin_id(db:Session, admin_id:str):
    return db.query(UA.Admin).filter(UA.Admin.id_code == admin_id).first()