from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import AdminUser, Job, LLMRequest, Session as DBSession, Prompt
from pydantic import BaseModel
import hashlib
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["admin"])

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    hashed = hashlib.sha256(data.password.encode()).hexdigest()
    admin = db.query(AdminUser).filter(
        AdminUser.email == data.email,
        AdminUser.password_hash == hashed
    ).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Простой токен (для MVP)
    token = hashlib.sha256(f"{admin.id}{datetime.now()}".encode()).hexdigest()
    
    return {"token": token, "email": admin.email}

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total_jobs = db.query(func.count(Job.id)).scalar()
    today_jobs = db.query(func.count(Job.id)).filter(
        Job.created_at >= datetime.now().date()
    ).scalar()
    
    success_jobs = db.query(func.count(Job.id)).filter(Job.status == 'done').scalar()
    
    total_tokens = db.query(func.sum(LLMRequest.tokens_used)).scalar() or 0
    cost = (total_tokens / 1_000_000) * 0.25  # Примерная стоимость
    
    # График последние 7 дней
    days = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = db.query(func.count(Job.id)).filter(
            func.date(Job.created_at) == date
        ).scalar()
        days.append({"date": str(date), "count": count})
    
    return {
        "total_jobs": total_jobs,
        "today_jobs": today_jobs,
        "success_rate": round(success_jobs / total_jobs * 100) if total_jobs > 0 else 0,
        "total_cost": round(cost, 2),
        "chart_data": days
    }

@router.get("/jobs")
async def get_jobs(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for job in jobs:
        session = db.query(DBSession).filter(DBSession.id == job.session_id).first()
        from app.models import Form
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        
        result.append({
            "id": job.id,
            "created_at": job.created_at.isoformat(),
            "status": job.status,
            "idea": form.payload.get('idea_description', '')[:100] if form else 'N/A'
        })
    
    return result

@router.get("/prompts")
async def get_prompts(db: Session = Depends(get_db)):
    prompts = db.query(Prompt).order_by(Prompt.track_name, Prompt.version.desc()).all()
    
    grouped = {}
    for p in prompts:
        if p.track_name not in grouped:
            grouped[p.track_name] = []
        grouped[p.track_name].append({
            "id": p.id,
            "version": p.version,
            "is_active": p.is_active,
            "prompt_template": p.prompt_template,
            "updated_at": p.updated_at.isoformat()
        })
    
    return grouped

class PromptUpdate(BaseModel):
    prompt_template: str

@router.post("/prompts/{prompt_id}/update")
async def update_prompt(prompt_id: int, data: PromptUpdate, db: Session = Depends(get_db)):
    old = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not old:
        raise HTTPException(404, "Prompt not found")
    
    # Деактивируем старую версию
    old.is_active = False
    
    # Создаем новую
    new = Prompt(
        track_name=old.track_name,
        prompt_template=data.prompt_template,
        params=old.params,
        version=old.version + 1,
        updated_by="admin",
        is_active=True
    )
    db.add(new)
    db.commit()
    
    return {"success": True, "new_version": new.version}

@router.get("/llm-logs")
async def get_llm_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(LLMRequest).order_by(LLMRequest.created_at.desc()).limit(limit).all()
    
    return [{
        "id": l.id,
        "track_id": l.track_id,
        "model": l.model,
        "tokens_used": l.tokens_used,
        "response_time_ms": l.response_time_ms,
        "status": l.status,
        "created_at": l.created_at.isoformat()
    } for l in logs]
