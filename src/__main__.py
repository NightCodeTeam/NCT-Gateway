try:
    import src
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))


import uvicorn
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from core.redis_client import RedisClient
from src.services import blocklist_service
from src.handlers.gateway import GatewayHandler

from src.settings import settings


redis_c = RedisClient(
    redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True),
    settings.REDIS_PREFIX,
    settings.REDIS_EXPIRE
)
gateway_handler = GatewayHandler(redis=redis_c)


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
async def gateway_handler(request: Request, path: str):
    """
    Основной обработчик всех запросов
    """
    try:

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


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
