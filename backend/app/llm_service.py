import os
import json
import time
import hashlib
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import LLMRequest, Track
import logging

logger = logging.getLogger(__name__)

# Инициализация OpenAI клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(
    prompt: str,
    form_data: dict,
    track_id: int,
    db: Session,
    model: str = None
) -> dict:
    """
    Вызывает LLM и сохраняет метрики в БД
    """
    model = model or os.getenv("LLM_MODEL", "gpt-4.1-nano")
    
    # Форматируем промпт
    formatted_prompt = prompt.format(**form_data)
    
    # Хеш промпта для логирования
    prompt_hash = hashlib.sha256(formatted_prompt.encode()).hexdigest()
    
    start_time = time.time()
    
    try:
        # Определяем параметры в зависимости от модели
        is_gpt5 = model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3") or model.startswith("o4")
        
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты эксперт-аналитик бизнес-идей. Отвечай только в формате JSON."},
                {"role": "user", "content": formatted_prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        if is_gpt5:
            params["max_completion_tokens"] = 2000
        else:
            params["max_tokens"] = 2000
            params["temperature"] = 0.7
        
        # Вызов OpenAI
        response = client.chat.completions.create(**params)
        
        # Время выполнения
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Получаем результат
        result_text = response.choices[0].message.content
        result_json = json.loads(result_text)
        
        # Логируем в БД
        llm_log = LLMRequest(
            track_id=track_id,
            prompt_hash=prompt_hash,
            model=model,
            tokens_used=response.usage.total_tokens,
            response_time_ms=response_time_ms,
            status="success"
        )
        db.add(llm_log)
        db.commit()
        
        logger.info(f"LLM success: track_id={track_id}, model={model}, tokens={response.usage.total_tokens}, time={response_time_ms}ms")
        
        return {
            "status": "success",
            "result": result_json,
            "tokens": response.usage.total_tokens,
            "response_time_ms": response_time_ms
        }
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Логируем ошибку
        llm_log = LLMRequest(
            track_id=track_id,
            prompt_hash=prompt_hash,
            model=model,
            tokens_used=0,
            response_time_ms=response_time_ms,
            status="error",
            error=str(e)
        )
        db.add(llm_log)
        db.commit()
        
        logger.error(f"LLM error: track_id={track_id}, error={str(e)}")
        
        return {
            "status": "error",
            "error": str(e),
            "response_time_ms": response_time_ms
        }
