from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Track, Report, Job, Form
from openai import OpenAI
import os
import json
from app.document_generator import generate_pdf, generate_docx
from app.s3_service import upload_to_s3

def consolidate_and_swot(job_id: int):
    db = SessionLocal()
    try:
        # Получаем треки
        tracks = db.query(Track).filter(Track.job_id == job_id, Track.status == "completed").all()
        if len(tracks) < 3:
            return None
        
        track_data = {}
        for t in tracks:
            # Извлекаем текстовый результат
            if isinstance(t.raw_output, dict) and 'result' in t.raw_output:
                track_data[t.track_name] = t.raw_output['result']
            else:
                track_data[t.track_name] = str(t.raw_output)
        
        # Промпт консолидации
        prompt = f"""Сформируй результат в формате аналитического отчета по трем полученным отчетам, увязанным в логическую цепочку для executives с буллетами на 3–5 страниц: больше связного текста и понятной структуры и bullets с ответом на вопрос "что из этого следует".

ОТЧЕТ 1 - АНАЛИЗ РЫНКОВ И НИШ:
{track_data.get('track1_market_analysis', 'Нет данных')}

ОТЧЕТ 2 - АНАЛИЗ АНАЛОГОВ И АНТИЛОГОВ:
{track_data.get('track2_growth_strategy', 'Нет данных')}

ОТЧЕТ 3 - АНАЛИЗ КЛИЕНТСКИХ БОЛЕЙ:
{track_data.get('track3_risks_analysis', 'Нет данных')}

После окончания отчета, не раньше, сделай анализ предлагаемых опций по критериям и выбери оптимальный вариант.

Структура ответа:
1. Executive Summary (2-3 абзаца) - главные выводы из всех трех анализов
2. Синтез ключевых инсайтов из трех направлений (bullets с конкретными выводами)
3. Стратегические рекомендации на основе всех анализов
4. Анализ опций и выбор оптимального варианта с обоснованием
5. Конкретные следующие шаги (action items)

Пиши на русском языке, структурированно, используй bullets для ключевых выводов."""

        # Вызываем OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4.1-nano"),
            messages=[
                {"role": "system", "content": "Ты стратегический консультант топ-уровня. Создаёшь executive отчеты для руководителей. Отвечай подробно, структурированно, с bullets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=16000
        )
        
        consolidation_text = response.choices[0].message.content
        
        # Формируем финальный отчет
        final_report = {
            "tracks": {
                "market_analysis": track_data.get('track1_market_analysis'),
                "growth_opportunities": track_data.get('track2_growth_strategy'),
                "risks_constraints": track_data.get('track3_risks_analysis')
            },
            "consolidation": {
                "executive_summary": consolidation_text
            }
        }
        
        # Генерируем PDF и DOCX
        os.makedirs("/app/reports", exist_ok=True)
        pdf_path = f"/app/reports/report_{job_id}.pdf"
        docx_path = f"/app/reports/report_{job_id}.docx"
        
        # Получаем исходные данные формы
        job = db.query(Job).filter(Job.id == job_id).first()
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        form_input = form.payload if form else {}
        
        generate_pdf(final_report, pdf_path, form_input)
        generate_docx(final_report, docx_path, form_input)
        
        # Загружаем в S3
        pdf_url = upload_to_s3(pdf_path, f"reports/report_{job_id}.pdf")
        docx_url = upload_to_s3(docx_path, f"reports/report_{job_id}.docx")
        
        # Сохраняем отчет в БД
        report = Report(
            job_id=job_id,
            report_json=final_report,
            pdf_url=pdf_url,
            docx_url=docx_url
        )
        db.add(report)
        db.commit()
        
        return final_report
        
    finally:
        db.close()