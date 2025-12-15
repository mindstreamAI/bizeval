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
            # Извлекаем result из {"status": "success", "result": {...}}
            if isinstance(t.raw_output, dict) and 'result' in t.raw_output:
                track_data[t.track_name] = t.raw_output['result']
            else:
                track_data[t.track_name] = t.raw_output
        
        # Получаем project_stage из формы
        job = db.query(Job).filter(Job.id == job_id).first()
        form = db.query(Form).filter(Form.session_id == job.session_id).first()
        project_stage = form.payload.get('project_stage', 'idea') if form else 'idea'
        
        # Детальный промпт консолидации
        prompt = f"""Ты эксперт-аналитик бизнес-идей. На основе трех углубленных анализов создай комплексный отчет.

ДАННЫЕ АНАЛИЗОВ:
1. ЦЕЛЕВАЯ АУДИТОРИЯ И PMF:
{json.dumps(track_data.get('track1_audience', {}), ensure_ascii=False, indent=2)}

2. ГЛОБАЛЬНАЯ КОНКУРЕНЦИЯ:
{json.dumps(track_data.get('track2_global', {}), ensure_ascii=False, indent=2)}

3. ЛОКАЛЬНЫЙ РЫНОК:
{json.dumps(track_data.get('track3_local', {}), ensure_ascii=False, indent=2)}

СТАДИЯ ПРОЕКТА: {project_stage}

ЗАДАЧА:
Синтезируй все данные в структурированный отчет следуя этим правилам:

1. EXECUTIVE SUMMARY (3-4 абзаца):
   - Основная суть идеи и ее потенциал
   - Ключевые выводы по аудитории
   - Конкурентная ситуация
   - Итоговая рекомендация (go/no-go/pivot)

2. AUDIENCE ANALYSIS:
   - key_segments: Выбери 3 самых приоритетных сегмента из анализа (только названия)
   - priority_segment: ОДИН главный приоритетный сегмент (с наивысшим fit_score)
   - market_fit_score: Используй overall_fit из анализа аудитории
   - key_insights: 3-4 ключевых инсайта о целевой аудитории

3. COMPETITIVE LANDSCAPE:
   - main_competitors: 3-4 главных глобальных конкурента (только названия)
   - competition_intensity: Используй competition_level из анализа
   - market_gaps: Незанятые ниши (2-3 пункта)
   - best_practices: 3 лучшие практики для адаптации

4. LOCAL MARKET:
   - key_trends: Ключевые локальные тренды (3-4 пункта)
   - local_competitors: 2-3 главных локальных конкурента (только названия)
   - market_attractiveness: Используй market_attractiveness из анализа
   - regional_specifics: Региональная специфика (2-3 пункта)

5. SWOT АНАЛИЗ (по 3-4 пункта в каждом квадранте):
   
   STRENGTHS - сформируй из:
   - Высокий fit_score сегментов аудитории
   - Уникальные преимущества идеи vs конкурентов
   - Незанятые ниши на рынке
   - Сильные стороны value proposition
   
   WEAKNESSES - сформируй из:
   - Сегменты с низким fit_score
   - Отставание от существующих конкурентов
   - Барьеры входа на рынок
   - Слабые стороны текущей стадии проекта
   
   OPPORTUNITIES - сформируй из:
   - Локальные тренды с растущим спросом
   - Незанятые ниши для захвата
   - Best practices конкурентов для адаптации
   - Возможности масштабирования
   
   THREATS - сформируй из:
   - Высокий уровень конкуренции
   - Локальные вызовы и препятствия
   - Сильные установленные конкуренты
   - Рыночные риски

6. STRATEGIC RECOMMENDATIONS (5-7 рекомендаций):
   Каждая рекомендация - объект с полями:
   - priority: "high" | "medium" | "low"
   - category: "product" | "marketing" | "business_model" | "risks"
   - recommendation: Конкретное действие (1-2 предложения)
   - rationale: Почему это важно (1 предложение)
   
   Распредели рекомендации по категориям:
   - product: что улучшить в продукте
   - marketing: как продвигать и позиционировать
   - business_model: как оптимизировать монетизацию
   - risks: какие риски нужно закрыть

7. OVERALL SCORE (число от 1 до 10):
   Рассчитай по формуле: (market_fit_score * 0.4) + ((11 - competition_intensity) * 0.3) + (market_attractiveness * 0.3)
   Округли до 0.5 (например: 6.8 → 7.0, 7.2 → 7.0, 7.3 → 7.5)
   Пример расчета: если market_fit_score=8, competition_intensity=7, market_attractiveness=8, то:
   (8 * 0.4) + ((11 - 7) * 0.3) + (8 * 0.3) = 3.2 + 1.2 + 2.4 = 6.8 → округлить до 7.0

8. RISK LEVEL:
   Определи на основе overall_score:
   - "low" если overall_score >= 8
   - "medium" если 5 <= overall_score < 8
   - "high" если overall_score < 5

9. INVESTMENT READINESS:
   Определи на основе стадии проекта ({project_stage}):
   - "idea_stage" если стадия = "idea"
   - "prototype_stage" если стадия = "prototype"
   - "market_ready" если стадия = "first_clients"
   - "scaling_ready" если стадия = "scale"

ВАЖНО: 
- Все тексты на русском языке
- Используй конкретные данные из анализов, не выдумывай
- SWOT должен быть сбалансированным и реалистичным
- Рекомендации должны быть конкретными и actionable

ФОРМАТ ОТВЕТА: Верни ТОЛЬКО валидный JSON без markdown разметки, без ```json блоков, без пояснений.

Структура JSON:
{{
  "executive_summary": "текст 3-4 абзаца",
  "audience_analysis": {{
    "key_segments": ["сегмент1", "сегмент2", "сегмент3"],
    "priority_segment": "название",
    "market_fit_score": число,
    "key_insights": ["инсайт1", "инсайт2", "инсайт3"]
  }},
  "competitive_landscape": {{
    "main_competitors": ["конкурент1", "конкурент2"],
    "competition_intensity": число,
    "market_gaps": ["ниша1", "ниша2"],
    "best_practices": ["практика1", "практика2"]
  }},
  "local_market": {{
    "key_trends": ["тренд1", "тренд2"],
    "local_competitors": ["компания1", "компания2"],
    "market_attractiveness": число,
    "regional_specifics": ["особенность1", "особенность2"]
  }},
  "swot": {{
    "strengths": ["s1", "s2", "s3"],
    "weaknesses": ["w1", "w2", "w3"],
    "opportunities": ["o1", "o2", "o3"],
    "threats": ["t1", "t2", "t3"]
  }},
  "strategic_recommendations": [
    {{
      "priority": "high",
      "category": "product",
      "recommendation": "текст",
      "rationale": "текст"
    }}
  ],
  "overall_score": число,
  "risk_level": "low|medium|high",
  "investment_readiness": "idea_stage|prototype_stage|market_ready|scaling_ready"
}}"""

        # Вызываем OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4.1-nano"),
            messages=[
                {"role": "system", "content": "Ты эксперт-аналитик бизнес-идей. Отвечаешь строго в формате JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=3000
        )
        
        # Парсим ответ
        consolidation = json.loads(response.choices[0].message.content)
        
        # Формируем финальный отчет
        final_report = {
            "tracks": {
                "audience": track_data.get('track1_audience'),
                "global_competitors": track_data.get('track2_global'),
                "local_market": track_data.get('track3_local')
            },
            "consolidation": consolidation
        }
        
        # Генерируем PDF и DOCX
        os.makedirs("/app/reports", exist_ok=True)
        pdf_path = f"/app/reports/report_{job_id}.pdf"
        docx_path = f"/app/reports/report_{job_id}.docx"
        
        generate_pdf(final_report, pdf_path)
        generate_docx(final_report, docx_path)
        
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
