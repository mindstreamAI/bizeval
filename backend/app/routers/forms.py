from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Form, Session as DBSession, Job
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/form", tags=["forms"])

class FormData(BaseModel):
    idea_description: str
    target_audience: str
    industry: str
    geography: str
    value_proposition: str
    monetization_model: str
    project_stage: str
    additional_comments: Optional[str] = None

class FormStructure(BaseModel):
    fields: list

@router.get("/structure", response_model=FormStructure)
async def get_form_structure():
    """Возвращает структуру формы анкеты"""
    fields = [
        {
            "name": "idea_description",
            "label": "Описание идеи",
            "type": "textarea",
            "required": True,
            "placeholder": "Опишите вашу бизнес-идею..."
        },
        {
            "name": "target_audience",
            "label": "Целевая аудитория",
            "type": "textarea",
            "required": True,
            "placeholder": "Кто ваши потенциальные клиенты?"
        },
        {
            "name": "industry",
            "label": "Индустрия",
            "type": "select",
            "required": True,
            "options": ["Tech", "E-commerce", "Healthcare", "Education", "Finance", "Other"]
        },
        {
            "name": "geography",
            "label": "География",
            "type": "select",
            "required": True,
            "options": ["Russia", "USA", "Europe", "Asia", "Global"]
        },
        {
            "name": "value_proposition",
            "label": "Ценностное предложение",
            "type": "textarea",
            "required": True,
            "placeholder": "Что уникального вы предлагаете?"
        },
        {
            "name": "monetization_model",
            "label": "Модель монетизации",
            "type": "textarea",
            "required": True,
            "placeholder": "Как планируете зарабатывать?"
        },
        {
            "name": "project_stage",
            "label": "Стадия проекта",
            "type": "radio",
            "required": True,
            "options": ["idea", "prototype", "first_clients", "scale"]
        },
        {
            "name": "additional_comments",
            "label": "Дополнительные комментарии",
            "type": "textarea",
            "required": False,
            "placeholder": "Любая дополнительная информация..."
        }
    ]
    
    return FormStructure(fields=fields)

@router.post("/submit/{session_id}")
async def submit_form(
    session_id: int,
    form_data: FormData,
    db: Session = Depends(get_db)
):
    """Отправка формы и запуск анализа через Celery"""
    # Проверяем существование сессии
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Сохраняем форму
    new_form = Form(
        session_id=session_id,
        payload=form_data.dict()
    )
    db.add(new_form)
    db.commit()
    db.refresh(new_form)
    
    # Создаем задание (job)
    new_job = Job(
        session_id=session_id,
        status="pending"
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    # Запускаем Celery задачу
    from app.tasks import run_full_analysis
    task = run_full_analysis.delay(new_job.id)
    
    return {
        "job_id": new_job.id,
        "task_id": task.id,
        "status": "pending",
        "message": "Анализ запущен в фоне"
    }
