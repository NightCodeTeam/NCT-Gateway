try:
    import src
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import logging

import uvicorn
import redis.asyncio as redis
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core.redis_client import RedisClient
from src.services import blocklist_service
from src.gateway.base import GatewayProcessor

from src.settings import settings


redis_c = RedisClient(
    redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True),
    settings.REDIS_PREFIX,
    settings.REDIS_EXPIRE
)
processor = GatewayProcessor(redis=redis_c)


app = FastAPI(
    title='NCT Gateway',
    version='0.1.0',
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
async def gateway_handler(request: Request):
    """
    Основной обработчик всех запросов
    """
    try:
        # Обработка запроса со всеми проверками
        return await processor.process_request(request)

    except Exception as e:
        logging.exception(f"Gateway error > e")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error'
        )


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
