from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import AdminUser, Job, LLMRequest, Session as DBSession, Prompt, Setting
from pydantic import BaseModel
import hashlib
from datetime import datetime, timedelta
import os

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
    cost = (total_tokens / 1_000_000) * 0.25
    
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
        from app.models import Form
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        
        # Берём industry_products из новой анкеты, или idea_description из старой
        idea_text = 'N/A'
        if form:
            idea_text = form.payload.get('industry_products', form.payload.get('idea_description', 'N/A'))[:100]
        
        result.append({
            "id": job.id,
            "created_at": job.created_at.isoformat(),
            "status": job.status,
            "idea": idea_text
        })
    
    return result

@router.get("/prompts")
async def get_prompts(db: Session = Depends(get_db)):
    # Показываем только новые треки
    new_tracks = ['track1_market_analysis', 'track2_growth_strategy', 'track3_risks_analysis']
    prompts = db.query(Prompt).filter(
        Prompt.track_name.in_(new_tracks)
    ).order_by(Prompt.track_name, Prompt.version.desc()).all()
    
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
    
    old.is_active = False
    
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

@router.get("/settings")
async def get_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}

class SettingUpdate(BaseModel):
    settings: dict

@router.post("/settings/update")
async def update_settings(data: SettingUpdate, db: Session = Depends(get_db)):
    for key, value in data.settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    
    db.commit()
    
    env_path = '/app/.env'
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    env_map = {
        's3_endpoint': 'S3_ENDPOINT',
        's3_access_key': 'S3_ACCESS_KEY',
        's3_secret_key': 'S3_SECRET_KEY',
        's3_bucket': 'S3_BUCKET',
        'openai_api_key': 'OPENAI_API_KEY',
        'llm_model': 'LLM_MODEL'
    }
    
    new_lines = []
    for line in lines:
        updated = False
        for key, env_var in env_map.items():
            if line.startswith(f'{env_var}=') and key in data.settings:
                new_lines.append(f'{env_var}={data.settings[key]}\n')
                updated = True
                break
        if not updated:
            new_lines.append(line)
    
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    return {"success": True, "message": "Настройки сохранены"}

@router.post("/restart-worker")
async def restart_worker():
    try:
        # Используем Docker socket
        import docker
        client = docker.from_env()
        container = client.containers.get('bizeval_worker')
        container.restart()
        return {"success": True, "message": "Worker перезапущен успешно"}
    except Exception as e:
        return {"success": False, "message": f"Ошибка: {str(e)}"}