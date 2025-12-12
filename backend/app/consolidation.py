import os
from openai import OpenAI
from app.database import SessionLocal
from app.models import Job, Track, Report
import logging

logger = logging.getLogger(__name__)

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def consolidate_and_swot(job_id: int):
    """
    Консолидирует результаты 3 треков и генерирует SWOT анализ
    """
    db = SessionLocal()
    
    try:
        # Получаем все треки
        tracks = db.query(Track).filter(
            Track.job_id == job_id,
            Track.status == "completed"
        ).all()
        
        if len(tracks) < 3:
            logger.warning(f"Job {job_id}: only {len(tracks)}/3 tracks completed")
            return None
        
        # Собираем данные из треков
        track_data = {}
        for track in tracks:
            track_data[track.track_name] = track.raw_output
        
        # Создаем промпт для консолидации + SWOT
        consolidation_prompt = f"""Ты эксперт-аналитик. У тебя есть результаты анализа бизнес-идеи по 3 направлениям:

ТРЕК 1 - АНАЛИЗ АУДИТОРИИ:
{track_data.get('track1_audience', {})}

ТРЕК 2 - ГЛОБАЛЬНЫЕ КОНКУРЕНТЫ:
{track_data.get('track2_global', {})}

ТРЕК 3 - ЛОКАЛЬНЫЙ РЫНОК:
{track_data.get('track3_local', {})}

Твоя задача:
1. Создать Executive Summary (2-3 абзаца) - главные выводы
2. Провести SWOT анализ на основе всех 3 треков
3. Дать 5 конкретных рекомендаций

ВАЖНО: Ответь ТОЛЬКО в формате JSON:
{{
  "executive_summary": "Краткое резюме всего анализа (2-3 абзаца)",
  "swot": {{
    "strengths": ["Сильная сторона 1", "Сильная сторона 2", "Сильная сторона 3"],
    "weaknesses": ["Слабость 1", "Слабость 2", "Слабость 3"],
    "opportunities": ["Возможность 1", "Возможность 2", "Возможность 3"],
    "threats": ["Угроза 1", "Угроза 2", "Угроза 3"]
  }},
  "recommendations": [
    "Рекомендация 1",
    "Рекомендация 2",
    "Рекомендация 3",
    "Рекомендация 4",
    "Рекомендация 5"
  ],
  "overall_score": 7
}}"""
        
        # Вызываем LLM
        client = get_openai_client()
        model = os.getenv("LLM_MODEL", "gpt-4.1-nano")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты эксперт-аналитик бизнес-идей. Отвечай только в формате JSON."},
                {"role": "user", "content": consolidation_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        import json
        consolidation_result = json.loads(response.choices[0].message.content)
        
        # Формируем итоговый отчет
        final_report = {
            "tracks": {
                "audience": track_data.get('track1_audience'),
                "global_competitors": track_data.get('track2_global'),
                "local_market": track_data.get('track3_local')
            },
            "consolidation": consolidation_result
        }
        
        # Сохраняем в БД
        report = Report(
            job_id=job_id,
            report_json=final_report
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        logger.info(f"Consolidation completed for job_id={job_id}, report_id={report.id}")
        
        return final_report
        
    except Exception as e:
        logger.error(f"Error in consolidate_and_swot: {str(e)}")
        return None
    
    finally:
        db.close()
