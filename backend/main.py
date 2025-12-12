from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import sessions, forms, analysis

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting BizEval API...")
    yield
    # Shutdown
    logger.info("Shutting down BizEval API...")

app = FastAPI(
    title="BizEval API",
    description="Business Idea Evaluation Service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(sessions.router)
app.include_router(forms.router)
app.include_router(analysis.router)

@app.get("/")
async def root():
    return {
        "message": "BizEval API is running",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "sessions": "/api/session",
            "forms": "/api/form",
            "analysis": "/api/analysis",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# WebSocket для реального времени
@app.websocket("/ws/{ws_token}")
async def websocket_endpoint(websocket: WebSocket, ws_token: str):
    await websocket.accept()
    logger.info(f"WebSocket connected: ws_token={ws_token}")
    
    try:
        await websocket.send_json({
            "type": "system_message",
            "message": f"Подключено к сессии {ws_token}"
        })
        
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received: {data}")
            
            await websocket.send_json({
                "type": "echo",
                "message": f"Получено: {data}"
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: ws_token={ws_token}")
