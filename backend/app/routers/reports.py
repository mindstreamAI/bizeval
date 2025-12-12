from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report, Job
import os

router = APIRouter(prefix="/api/report", tags=["reports"])

@router.get("/{job_id}")
async def get_report(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    report = db.query(Report).filter(Report.job_id == job_id).first()
    
    if not report:
        if job.status in ["pending", "running"]:
            return {"job_id": job_id, "status": job.status, "message": "В процессе"}
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {
        "job_id": job_id,
        "status": job.status,
        "report": report.report_json,
        "files": {
            "pdf": f"/api/report/{job_id}/download/pdf",
            "docx": f"/api/report/{job_id}/download/docx"
        }
    }

@router.get("/{job_id}/download/{file_type}")
async def download_file(job_id: int, file_type: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.job_id == job_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if file_type == "pdf":
        path = report.pdf_url
        media = "application/pdf"
        filename = f"bizeval_report_{job_id}.pdf"
    elif file_type == "docx":
        path = report.docx_url
        media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"bizeval_report_{job_id}.docx"
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path, media_type=media, filename=filename)
