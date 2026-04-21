from sqlalchemy import Column, String, Integer, Boolean, DateTime, func
from app.db.postgres import Base

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True)
    endpoint = Column(String, nullable=False, unique=True)
    algorithm = Column(String, nullable=False)  # "token_bucket" | "sliding_window"
    limit = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=True)
    ip = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    allowed = Column(Boolean, nullable=False)
    algorithm = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())