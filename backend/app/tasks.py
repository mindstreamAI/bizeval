from celery import chord
from celery_app import celery_app
from app.database import SessionLocal
from app.models import Job, Track, LLMRequest, Prompt
from app.llm_service import call_llm
from app.consolidation import consolidate_and_swot
import logging
import redis
import json

logger = logging.getLogger(__name__)
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def publish_status(session_id: int, status: str, message: str, data: dict = None):
    """Публикуем статус в Redis для WebSocket"""
    payload = {
        "type": status,
        "message": message,
        "data": data or {}
    }
    redis_client.publish(f"session:{session_id}", json.dumps(payload))
    logger.info(f"Published to session:{session_id}: {message}")

@celery_app.task(bind=True)
def analyze_track(self, job_id: int, session_id: int, track_name: str, form_data: dict):
    db = SessionLocal()
    
    # Русские названия треков
    track_labels = {
        'track1_market_analysis': '📊 Анализ рынков и ниш',
        'track2_growth_strategy': '🔍 Анализ аналогов и антилогов', 
        'track3_risks_analysis': '💡 Анализ клиентских болей'
    }
    
    try:
        publish_status(session_id, "track_started", f"📄 {track_labels.get(track_name, track_name)}...")
        
        # Получаем активный промпт
        prompt_obj = db.query(Prompt).filter(
            Prompt.track_name == track_name,
            Prompt.is_active == True
        ).first()
        
        if not prompt_obj:
            raise Exception(f"No active prompt for {track_name}")
        
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
        result = call_llm(
            prompt=prompt_obj.prompt_template,
            form_data=form_data,
            track_id=track.id,
            db=db
        )
        
        if result:
            track.status = "completed"
            track.raw_output = result
            db.commit()
            
            publish_status(session_id, "track_completed", f"✅ {track_labels.get(track_name, track_name)} завершен", {"track": track_name})
            return {"success": True, "track_name": track_name}
        else:
            track.status = "failed"
            db.commit()
            publish_status(session_id, "track_failed", f"❌ {track_labels.get(track_name, track_name)} ошибка")
            return {"success": False, "track_name": track_name}
            
    except Exception as e:
        logger.error(f"Track {track_name} error: {e}")
        publish_status(session_id, "track_failed", f"❌ {track_labels.get(track_name, track_name)} ошибка: {str(e)}")
        return {"success": False, "track_name": track_name, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def finalize_analysis(self, results, job_id: int, session_id: int):
    """Финализация анализа"""
    db = SessionLocal()
    try:
        publish_status(session_id, "consolidation_started", "📄 Формирую итоговое резюме...")
        
        success_count = sum(1 for r in results if r.get('success'))
        logger.info(f"Finalize job {job_id}: {success_count}/3 tracks succeeded")
        
        if success_count >= 3:
            report = consolidate_and_swot(job_id)
            
            if report:
                job = db.query(Job).filter(Job.id == job_id).first()
                job.status = "done"
                db.commit()
                
                logger.info(f"Job {job_id} completed successfully")
                publish_status(session_id, "analysis_completed", "🎉 Анализ завершен!", {
                    "job_id": job_id,
                    "report": report
                })
                
                return {"job_id": job_id, "status": "done"}
            else:
                job = db.query(Job).filter(Job.id == job_id).first()
                job.status = "failed"
                db.commit()
                logger.error(f"Job {job_id} consolidation failed")
                publish_status(session_id, "analysis_failed", "❌ Ошибка при создании отчета")
        else:
            job = db.query(Job).filter(Job.id == job_id).first()
            job.status = "partial"
            db.commit()
            logger.warning(f"Job {job_id} partially completed: {success_count}/3")
            publish_status(session_id, "analysis_partial", f"⚠️ Завершено частично: {success_count}/3 треков")
            
        return {"job_id": job_id}
        
    except Exception as e:
        logger.error(f"Finalize error for job {job_id}: {e}", exc_info=True)
        publish_status(session_id, "analysis_failed", f"❌ Ошибка финализации: {str(e)}")
        return {"job_id": job_id, "status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True)
def run_full_analysis(self, job_id: int, session_id: int, form_data: dict):
    try:
        publish_status(session_id, "analysis_started", "🚀 Запускаю параллельный анализ по 3 направлениям...")
        
        track_tasks = [
            analyze_track.s(job_id, session_id, 'track1_market_analysis', form_data),
            analyze_track.s(job_id, session_id, 'track2_growth_strategy', form_data),
            analyze_track.s(job_id, session_id, 'track3_risks_analysis', form_data)
        ]
        
        callback = finalize_analysis.s(job_id, session_id)
        chord(track_tasks)(callback)
        
    except Exception as e:
        logger.error(f"run_full_analysis error: {e}", exc_info=True)
        publish_status(session_id, "analysis_failed", f"❌ Ошибка запуска: {str(e)}")