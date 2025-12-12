import os
from openai import OpenAI
from app.database import SessionLocal
from app.models import Job, Track, Report
from app.document_generator import generate_pdf, generate_docx
from app.s3_service import upload_to_s3
import logging

logger = logging.getLogger(__name__)

def consolidate_and_swot(job_id: int):
    db = SessionLocal()
    try:
        tracks = db.query(Track).filter(Track.job_id == job_id, Track.status == "completed").all()
        if len(tracks) < 3:
            return None
        
        track_data = {t.track_name: t.raw_output for t in tracks}
        
        prompt = f"""Анализ по 3 направлениям:
АУДИТОРИЯ: {track_data.get('track1_audience', {})}
КОНКУРЕНТЫ: {track_data.get('track2_global', {})}
РЫНОК: {track_data.get('track3_local', {})}

Создай JSON:
{{"executive_summary": "текст", "swot": {{"strengths": ["s1","s2","s3"], "weaknesses": ["w1","w2","w3"], "opportunities": ["o1","o2","o3"], "threats": ["t1","t2","t3"]}}, "recommendations": ["r1","r2","r3","r4","r5"], "overall_score": 7}}"""
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4.1-nano"),
            messages=[
                {"role": "system", "content": "Эксперт-аналитик. JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )
        
        import json
        consolidation = json.loads(response.choices[0].message.content)
        
        final_report = {
            "tracks": {
                "audience": track_data.get('track1_audience'),
                "global_competitors": track_data.get('track2_global'),
                "local_market": track_data.get('track3_local')
            },
            "consolidation": consolidation
        }
        
        os.makedirs("/app/reports", exist_ok=True)
        pdf_path = f"/app/reports/report_{job_id}.pdf"
        docx_path = f"/app/reports/report_{job_id}.docx"
        
        generate_pdf(final_report, pdf_path)
        generate_docx(final_report, docx_path)
        
        # Загружаем в S3
        pdf_url = upload_to_s3(pdf_path, f"reports/report_{job_id}.pdf")
        docx_url = upload_to_s3(docx_path, f"reports/report_{job_id}.docx")
        
        report = Report(job_id=job_id, report_json=final_report, pdf_url=pdf_url, docx_url=docx_url)
        db.add(report)
        db.commit()
        
        logger.info(f"Report {job_id} with S3 URLs")
        return final_report
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    finally:
        db.close()
