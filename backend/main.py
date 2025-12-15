from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import redis.asyncio as aioredis
import json
import asyncio

from app.routers import sessions, forms, analysis, reports, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logger.info("Starting BizEval API...")
    redis_client = await aioredis.from_url("redis://redis:6379", decode_responses=True)
    yield
    await redis_client.close()
    logger.info("Shutting down BizEval API...")

app = FastAPI(
    title="BizEval API",
    description="Business Idea Evaluation Service",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(forms.router)
app.include_router(analysis.router)
app.include_router(reports.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "message": "BizEval API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "sessions": "/api/session",
            "forms": "/api/form",
            "analysis": "/api/analysis",
            "reports": "/api/report",
            "admin": "/api/admin",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: session_id={session_id}")
    
    # Подписываемся на канал сессии
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"session:{session_id}")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Подключено к сессии {session_id}"
        })
        
        # Слушаем Redis и отправляем в WebSocket
        async def redis_listener():
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await websocket.send_json(data)
        
        # Слушаем WebSocket от клиента
        async def ws_receiver():
            while True:
                data = await websocket.receive_text()
                logger.info(f"Received from client: {data}")
        
        # Запускаем обе задачи параллельно
        await asyncio.gather(redis_listener(), ws_receiver())
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session_id={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe(f"session:{session_id}")
        await pubsub.close()
