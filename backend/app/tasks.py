from celery import group, chord
from celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, Track, Prompt, Form
from app.llm_service import call_llm
from app.consolidation import consolidate_and_swot
from app.websocket import publish_status
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.analyze_track")
def analyze_track(job_id: int, track_name: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "error"}
        
        publish_status(job.session_id, "running", f"Анализирую {track_name}...")
        
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        prompt_record = db.query(Prompt).filter(Prompt.track_name == track_name, Prompt.is_active == True).first()
        
        track = Track(job_id=job_id, track_name=track_name, status="running")
        db.add(track)
        db.commit()
        db.refresh(track)
        
        llm_result = call_llm(prompt_record.prompt_template, form.payload, track.id, db)
        
        if llm_result["status"] == "success":
            track.status = "completed"
            track.raw_output = llm_result["result"]
            publish_status(job.session_id, "track_completed", f"✅ {track_name}")
            result = {"status": "success", "track_name": track_name}
        else:
            track.status = "failed"
            result = {"status": "error"}
        
        db.commit()
        return result
    finally:
        db.close()

@celery_app.task(name="app.tasks.finalize_analysis")
def finalize_analysis(results, job_id):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        successful = [r for r in results if r.get("status") == "success"]
        
        if len(successful) == 3:
            job.status = "done"
            publish_status(job.session_id, "consolidating", "Формирую SWOT...")
            consolidate_and_swot(job_id)
            publish_status(job.session_id, "completed", "🎉 Готово!")
        else:
            job.status = "partial" if successful else "failed"
        
        db.commit()
        return {"job_id": job_id}
    finally:
        db.close()

@celery_app.task(name="app.tasks.run_full_analysis")
def run_full_analysis(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = "running"
        db.commit()
        
        publish_status(job.session_id, "started", "Запускаю...")
        
        tracks = ["track1_audience", "track2_global", "track3_local"]
        chord(group([analyze_track.s(job_id, t) for t in tracks]))(finalize_analysis.s(job_id))
        return {"job_id": job_id}
    finally:
        db.close()
