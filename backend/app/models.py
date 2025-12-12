from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(String(50), default="active")
    source_ip = Column(String(50))
    ws_token = Column(String(255), unique=True, index=True)

class Form(Base):
    __tablename__ = "forms"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    payload = Column(JSON)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    status = Column(String(50), default="pending", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    track_name = Column(String(100))
    status = Column(String(50), default="pending")
    raw_output = Column(JSON)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    report_json = Column(JSON)
    pdf_url = Column(String(500), nullable=True)
    docx_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Prompt(Base):
    __tablename__ = "prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    track_name = Column(String(100), index=True)
    prompt_template = Column(Text)
    params = Column(JSON)
    version = Column(Integer, default=1)
    updated_by = Column(String(100))
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(String(50), default="admin")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LLMRequest(Base):
    __tablename__ = "llm_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=True)
    prompt_hash = Column(String(64))
    model = Column(String(100))
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    status = Column(String(50))
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
