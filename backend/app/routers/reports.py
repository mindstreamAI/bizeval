from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report, Job

router = APIRouter(prefix="/api/report", tags=["reports"])

@router.get("/{job_id}")
async def get_report(job_id: int, db: Session = Depends(get_db)):
    """Получить полный отчет по job_id"""
    
    # Проверяем статус job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Ищем отчет
    report = db.query(Report).filter(Report.job_id == job_id).first()
    
    if not report:
        if job.status == "pending" or job.status == "running":
            return {
                "job_id": job_id,
                "status": job.status,
                "message": "Анализ еще выполняется"
            }
        else:
            raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "job_id": job_id,
        "status": job.status,
        "report": report.report_json
    }
