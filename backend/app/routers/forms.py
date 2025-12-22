from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Form, Session as DBSession, Job
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/form", tags=["forms"])

class FormData(BaseModel):
    industry_products: str
    customers: str
    business_model: str
    geography: str
    constraints: Optional[str] = None
    strategic_goals: Optional[str] = None
    additional_info: Optional[str] = None

class FormStructure(BaseModel):
    fields: list

@router.get("/structure", response_model=FormStructure)
async def get_form_structure():
    """Возвращает структуру формы анкеты"""
    fields = [
        {
            "name": "industry_products",
            "label": "Отрасль, продукты и услуги",
            "type": "textarea",
            "placeholder": "Опишите вашу отрасль, ключевые продукты/услуги и чем вы реально помогаете клиентам...",
            "required": True
        },
        {
            "name": "customers",
            "label": "Клиенты и их задачи",
            "type": "textarea",
            "placeholder": "Кто ваши клиенты (типы, размеры, сегменты) и какие задачи (jobs-to-be-done) они решают с вашей помощью...",
            "required": True
        },
        {
            "name": "business_model",
            "label": "Бизнес-модель и монетизация",
            "type": "textarea",
            "placeholder": "Как вы зарабатываете деньги: источники выручки, ключевые форматы, модель ценообразования...",
            "required": True
        },
        {
            "name": "geography",
            "label": "География",
            "type": "textarea",
            "placeholder": "В каких странах/регионах вы работаете и какие географии считаете потенциальными...",
            "required": True
        },
        {
            "name": "constraints",
            "label": "Ограничения",
            "type": "textarea",
            "placeholder": "Ваши ограничения: ресурсы, команда, технологии, регуляция, время основателя и т.п.",
            "required": False
        },
        {
            "name": "strategic_goals",
            "label": "Стратегические цели и амбиции",
            "type": "textarea",
            "placeholder": "Ваши стратегические цели, амбиции, видение развития...",
            "required": False
        },
        {
            "name": "additional_info",
            "label": "Дополнительная информация",
            "type": "textarea",
            "placeholder": "Любые дополнительные детали, которые считаете важными для выбора новых ниш, рынков и направлений роста...",
            "required": False
        }
    ]
    return {"fields": fields}

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
    
    # Запускаем Celery задачу с правильными параметрами
    from app.tasks import run_full_analysis
    task = run_full_analysis.delay(new_job.id, session_id, form_data.dict())
    
    return {
        "job_id": new_job.id,
        "task_id": task.id,
        "status": "pending",
        "message": "Анализ запущен в фоне"
    }