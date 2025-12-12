import redis
import json
import os

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))

def publish_status(session_id: int, status: str, message: str):
    """Публикует статус в Redis для WebSocket"""
    redis_client.publish(
        f"session:{session_id}",
        json.dumps({"type": "status_update", "status": status, "message": message})
    )
