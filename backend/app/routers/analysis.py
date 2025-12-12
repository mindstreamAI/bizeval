from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Form, Job, Track, Prompt
from app.llm_service import call_llm
import logging

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)

@router.post("/test/{job_id}")
async def test_analysis(job_id: int, db: Session = Depends(get_db)):
    """
    Тестовый endpoint - запускает анализ по job_id
    Выполняет 3 трека последовательно (пока без Celery)
    """
    # Находим job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Находим форму
    form = db.query(Form).filter(Form.session_id == job.session_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    form_data = form.payload
    
    # Обновляем статус job
    job.status = "running"
    db.commit()
    
    results = {}
    
    # Запускаем 3 трека
    track_names = ["track1_audience", "track2_global", "track3_local"]
    
    for track_name in track_names:
        logger.info(f"Starting {track_name} for job_id={job_id}")
        
        # Получаем активный промпт
        prompt_record = db.query(Prompt).filter(
            Prompt.track_name == track_name,
            Prompt.is_active == True
        ).first()
        
        if not prompt_record:
            logger.error(f"No active prompt found for {track_name}")
            continue
        
        # Создаем запись трека
        track = Track(
            job_id=job_id,
            track_name=track_name,
            status="running"
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        # Вызываем LLM
        llm_result = call_llm(
            prompt=prompt_record.prompt_template,
            form_data=form_data,
            track_id=track.id,
            db=db
        )
        
        if llm_result["status"] == "success":
            track.status = "completed"
            track.raw_output = llm_result["result"]
            results[track_name] = llm_result["result"]
        else:
            track.status = "failed"
            track.error = llm_result.get("error", "Unknown error")
        
        db.commit()
        logger.info(f"Completed {track_name}: status={track.status}")
    
    # Обновляем статус job
    job.status = "done" if len(results) == 3 else "partial"
    db.commit()
    
    return {
        "job_id": job_id,
        "status": job.status,
        "tracks_completed": len(results),
        "results": results
    }
