from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey
from datetime import datetime
from app.db.database import Base

class Election(Base):
    __tablename__= "elections"

    id = Column(String, primary_key=True, index=True)
    title= Column(String)
    short_name = Column(String)
    category = Column(String)
    status = Column(String) 
    start_date = Column(DateTime)
    start_time= Column(Time)
    end_date= Column(DateTime)
    end_time= Column(Time)
    # metadata
    created_at= Column(DateTime, default=datetime.utcnow)
    updated_at= Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vote_count = Column(Integer, default=0, index=True)
    status_flag = Column(String, default="closed")
