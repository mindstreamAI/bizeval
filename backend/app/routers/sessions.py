from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Session as DBSession
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/session", tags=["sessions"])

class SessionResponse(BaseModel):
    session_id: int
    ws_token: str
    status: str

@router.post("/start", response_model=SessionResponse)
async def start_session(db: Session = Depends(get_db)):
    """Создает новую сессию и возвращает ws_token"""
    ws_token = str(uuid.uuid4())
    
    new_session = DBSession(
        ws_token=ws_token,
        status="active",
        source_ip="0.0.0.0"  # TODO: получать реальный IP
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return SessionResponse(
        session_id=new_session.id,
        ws_token=ws_token,
        status=new_session.status
    )

@router.get("/{session_id}/status")
async def get_session_status(session_id: int, db: Session = Depends(get_db)):
    """Получить статус сессии"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.id,
        "status": session.status,
        "created_at": session.created_at
    }
