from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import os

# PostgreSQL connection
# format: postgresql://user:password@host:port/dbname
# Docker mein environment variable se aayega
# Local mein default use hoga
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing")

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class AccessLog(Base):
    __tablename__ = "access_logs"

    id         = Column(Integer, primary_key=True, index=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    email      = Column(String)    # kaun aaya
    role       = Column(String)    # hr / finance / admin
    path       = Column(String)    # /hr-portal, /finance
    device_id  = Column(String)    # kaun sa device
    allowed    = Column(Boolean)   # allow hua ya block
    blocked_at = Column(String)    # auth / device / policy
    reason     = Column(String)    # kyun block hua

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("PostgreSQL connected!")
        print("access_logs table ready!")
    except Exception as e:
        print(f" Database error: {e}")
        raise