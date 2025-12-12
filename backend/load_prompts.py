import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import Prompt

PROMPTS = {
    "track1_audience": """Ты эксперт по анализу целевой аудитории и Product-Market Fit.

Проанализируй бизнес-идею и целевую аудиторию:

ИДЕЯ: {idea_description}
АУДИТОРИЯ: {target_audience}
ИНДУСТРИЯ: {industry}
ГЕОГРАФИЯ: {geography}
ЦЕННОСТЬ: {value_proposition}

Твоя задача:
1. Определи 3-5 сегментов целевой аудитории (с характеристиками)
2. Для каждого сегмента опиши главные боли/потребности
3. Оцени Product-Market Fit по шкале 1-10 для каждого сегмента
4. Дай рекомендации по приоритизации сегментов

ВАЖНО: Ответь ТОЛЬКО в формате JSON без дополнительного текста:
{{
  "segments": [
    {{
      "name": "Название сегмента",
      "description": "Описание (2-3 предложения)",
      "size_estimate": "Примерный размер рынка",
      "pains": ["Боль 1", "Боль 2", "Боль 3"],
      "fit_score": 8,
      "priority": "high|medium|low"
    }}
  ],
  "overall_fit": 7,
  "recommendations": ["Рекомендация 1", "Рекомендация 2"]
}}""",

    "track2_global": """Ты эксперт по конкурентному анализу и глобальным рынкам.

Проанализируй конкурентную среду для этой идеи:

ИДЕЯ: {idea_description}
ИНДУСТРИЯ: {industry}
ГЕОГРАФИЯ: {geography}
МОНЕТИЗАЦИЯ: {monetization_model}
СТАДИЯ: {project_stage}

Твоя задача:
1. Найди 3-7 глобальных конкурентов (реальные компании)
2. Опиши их сильные стороны и модели монетизации
3. Определи best practices из индустрии
4. Оцени уровень конкуренции (1-10)

ВАЖНО: Ответь ТОЛЬКО в формате JSON без дополнительного текста:
{{
  "competitors": [
    {{
      "name": "Название компании",
      "description": "Что делают (1-2 предложения)",
      "strengths": ["Сила 1", "Сила 2"],
      "monetization": "Как зарабатывают",
      "market_position": "Позиция на рынке"
    }}
  ],
  "best_practices": ["Практика 1", "Практика 2", "Практика 3"],
  "competition_level": 7,
  "barriers_to_entry": ["Барьер 1", "Барьер 2"]
}}""",

    "track3_local": """Ты эксперт по локальным рынкам и региональной специфике.

Проанализируй локальный рынок для этой идеи:

ИДЕЯ: {idea_description}
ГЕОГРАФИЯ: {geography}
АУДИТОРИЯ: {target_audience}
СТАДИЯ: {project_stage}
КОММЕНТАРИИ: {additional_comments}

Твоя задача:
1. Найди 3-5 локальных конкурентов в регионе {geography}
2. Опиши локальные тренды и особенности рынка
3. Определи незанятые ниши
4. Оцени привлекательность локального рынка (1-10)

ВАЖНО: Ответь ТОЛЬКО в формате JSON без дополнительного текста:
{{
  "local_competitors": [
    {{
      "name": "Название компании",
      "description": "Что делают",
      "market_share": "Примерная доля рынка"
    }}
  ],
  "local_trends": ["Тренд 1", "Тренд 2", "Тренд 3"],
  "untapped_niches": ["Ниша 1", "Ниша 2"],
  "market_attractiveness": 8,
  "local_challenges": ["Вызов 1", "Вызов 2"]
}}"""
}

def load_prompts():
    db = SessionLocal()
    
    for track_name, prompt_text in PROMPTS.items():
        # Проверяем существует ли уже активный промпт
        existing = db.query(Prompt).filter(
            Prompt.track_name == track_name,
            Prompt.is_active == True
        ).first()
        
        if existing:
            print(f"⚠️  Промпт {track_name} уже существует (версия {existing.version})")
            continue
        
        # Создаем новый промпт
        new_prompt = Prompt(
            track_name=track_name,
            prompt_template=prompt_text,
            params={"temperature": 0.7, "max_tokens": 2000},
            version=1,
            updated_by="system",
            is_active=True
        )
        
        db.add(new_prompt)
        print(f"✅ Создан промпт: {track_name} (версия 1)")
    
    db.commit()
    print(f"\n✅ Промпты загружены в БД!")
    db.close()

if __name__ == "__main__":
    load_prompts()
