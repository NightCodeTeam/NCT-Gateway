try:
    import src
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from contextlib import asynccontextmanager

import uvicorn
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core.redis_client import RedisClient
from src.database import init_db
from src.services import blocklist_service

from src.settings import settings


redis_c = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    app.state.redis = RedisClient(
        redis_pool=redis_c,
        prefix=settings.REDIS_PREFIX,
        expire=settings.REDIS_EXPIRE
    )
    yield


app = FastAPI(
    title='NCT Gateway',
    version='0.1.0',
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_URL.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def gateway_handler(request: Request, path: str):
    """
    Основной обработчик всех запросов
    """
    try:
        # Создание процессора
        processor = GatewayProcessor(request)

        # Обработка запроса со всеми проверками
        return await processor.process_request()

    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        logging.exception("Gateway error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )


@app.middleware('http')
async def blocker(request: Request, call_next):
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
