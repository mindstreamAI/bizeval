import os
import json
import time
import hashlib
from openai import OpenAI
from sqlalchemy.orm import Session
from app.models import LLMRequest, Track
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(
    prompt: str,
    form_data: dict,
    track_id: int,
    db: Session,
    model: str = None
) -> dict:
    """Вызывает LLM и сохраняет метрики в БД"""
    model = model or os.getenv("LLM_MODEL", "gpt-4.1-nano")
    
    formatted_prompt = prompt.format(**form_data)
    prompt_hash = hashlib.sha256(formatted_prompt.encode()).hexdigest()
    
    start_time = time.time()
    
    try:
        is_gpt5 = model.startswith("gpt-5") or model.startswith("o1") or model.startswith("o3") or model.startswith("o4")
        
        params = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты стратегический консультант. Отвечай подробно, структурированно, используй bullets и нумерованные списки. НИКОГДА не используй ASCII-таблицы (|---|---), вместо них используй простые нумерованные списки или bullets с отступами."},
                {"role": "user", "content": formatted_prompt}
            ]
        }
        
        if is_gpt5:
            params["max_completion_tokens"] = 16000
        else:
            params["max_tokens"] = 16000
            params["temperature"] = 0.7
        
        response = client.chat.completions.create(**params)
        response_time_ms = int((time.time() - start_time) * 1000)
        result_text = response.choices[0].message.content
        
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
        
        logger.info(f"LLM success: track_id={track_id}, tokens={response.usage.total_tokens}, time={response_time_ms}ms")
        
        return {
            "status": "success",
            "result": result_text,
            "tokens": response.usage.total_tokens,
            "response_time_ms": response_time_ms
        }
        
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        
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