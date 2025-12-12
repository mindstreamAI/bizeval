from celery import group, chord
from celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, Track, Prompt, Report, Form
from app.llm_service import call_llm
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.analyze_track")
def analyze_track(job_id: int, track_name: str):
    """Анализирует один трек (запускается параллельно)"""
    db = SessionLocal()
    
    try:
        logger.info(f"Starting {track_name} for job_id={job_id}")
        
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"status": "error", "error": "Job not found"}
        
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        if not form:
            logger.error(f"Form for job {job_id} not found")
            return {"status": "error", "error": "Form not found"}
        
        form_data = form.payload
        
        prompt_record = db.query(Prompt).filter(
            Prompt.track_name == track_name,
            Prompt.is_active == True
        ).first()
        
        if not prompt_record:
            logger.error(f"No active prompt for {track_name}")
            return {"status": "error", "error": "No active prompt"}
        
        track = Track(
            job_id=job_id,
            track_name=track_name,
            status="running"
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        
        llm_result = call_llm(
            prompt=prompt_record.prompt_template,
            form_data=form_data,
            track_id=track.id,
            db=db
        )
        
        if llm_result["status"] == "success":
            track.status = "completed"
            track.raw_output = llm_result["result"]
            result = {
                "status": "success",
                "track_name": track_name,
                "result": llm_result["result"]
            }
        else:
            track.status = "failed"
            track.error = llm_result.get("error", "Unknown error")
            result = {
                "status": "error",
                "track_name": track_name,
                "error": llm_result.get("error")
            }
        
        db.commit()
        logger.info(f"Completed {track_name}: status={track.status}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in {track_name}: {str(e)}")
        return {"status": "error", "track_name": track_name, "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.finalize_analysis")
def finalize_analysis(results, job_id):
    """Финализирует анализ после завершения всех треков"""
    db = SessionLocal()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"status": "error", "error": "Job not found"}
        
        successful = [r for r in results if r.get("status") == "success"]
        
        if len(successful) == 3:
            job.status = "done"
        elif len(successful) > 0:
            job.status = "partial"
        else:
            job.status = "failed"
        
        db.commit()
        
        logger.info(f"Job {job_id} finalized: {len(successful)}/3 tracks successful, status={job.status}")
        
        return {
            "job_id": job_id,
            "status": job.status,
            "tracks_completed": len(successful),
            "total_tracks": 3
        }
        
    except Exception as e:
        logger.error(f"Error in finalize_analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_full_analysis")
def run_full_analysis(job_id: int):
    """Запускает все 3 трека параллельно через chord"""
    db = SessionLocal()
    
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "error", "error": "Job not found"}
        
        job.status = "running"
        db.commit()
        
        track_names = ["track1_audience", "track2_global", "track3_local"]
        
        # Используем chord: параллельно запускаем треки, потом финализация
        callback = finalize_analysis.s(job_id)
        header = group([analyze_track.s(job_id, track_name) for track_name in track_names])
        
        result = chord(header)(callback)
        
        logger.info(f"Job {job_id} started with task_id={result.id}")
        
        return {"job_id": job_id, "task_id": result.id, "status": "running"}
        
    except Exception as e:
        logger.error(f"Error in run_full_analysis: {str(e)}")
        job.status = "failed"
        db.commit()
        return {"status": "error", "error": str(e)}
    
    finally:
        db.close()
