import os
import json
from dataclasses import dataclass

import httpx
from fastapi import Request, HTTPException, status
from fastapi.responses import StreamingResponse

from core.redis_client import RedisClient

from src.services.blocklist import blocklist_service

from .limiter import TokenBucket
from .exceptions import AppFileNotExist, AppsNotProvided


@dataclass(frozen=True, slots=True)
class App:
    name: str
    redirect_url: str

    blocker_check: bool = True
    auth_only: bool = False
    allowed_methods: tuple[str, ...] = ()
    unacceptable_paths: tuple[str, ...] = ('/.env',)

    max_rpm: int = 500


class GatewayProcessor:
    """
    Обработчик входящих запросов и валидации.
    Требуется в файле apps.json указать список подключенных приложений
    """
    __apps: dict[str, App] = {}
    __timers: dict[str, TokenBucket] = {}
    __client = httpx.AsyncClient(timeout=30.0)

    def __init__(
        self,
        redis: RedisClient,
        apps: tuple[App, ...] | None = None,
        apps_path: str | None = None,
    ):
        self.__redis = redis
        if apps is not None:
            self.__apps = {app.name: app for app in apps}
        else:
            if apps_path is None:
                raise AppsNotProvided()
            self.__load_apps(apps_path)

    def __load_apps(self, apps_path: str):
        """
        Подгружаем список приложений из apps.json.
        """
        if not os.path.exists(apps_path):
            raise AppFileNotExist('apps.json')

        with open('apps.json') as f:
            data = json.load(f)
            for app in data['apps']:
                prepared_app = App(**app)
                self.__apps[app['name']] = prepared_app
                self.__timers[app['name']] = TokenBucket(prepared_app.max_rpm)

    def __find_app(self, request: Request) -> App:
        """
        Забираем заголовок app_redirect из nginx и ищем соответствующее приложение.
        Если приложение не найдено, выбрасываем исключение 400.
        """
        app = self.__apps.get(request.headers.get('app_redirect', ''), None)
        if app:
            return app
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Incorrect request'
        )

    def __get_client_ip(self, request: Request) -> str:
        """
        Получаем IP клиента из запроса. Если IP не найден, выбрасываем исключение 400.
        """
        if request.client:
            return request.client.host
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Incorrect request'
        )

    @staticmethod
    def __check_allowed_method(request: Request, app: App) -> None:
        """
        Проверка что метод запроса разрешен приложением.
        """
        if len(app.allowed_methods) == 0:
            return
        if request.method not in app.allowed_methods:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail='Method not allowed'
            )

    def __check_timer(self, app: App) -> None:
        """
        Проверка максимального количества запросов.
        """
        if not self.__timers[app.name].consume():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    async def __check_unacceptable_path(self, request: Request, app: App, client_ip: str) -> None:
        """
        Проверка что путь запроса разрешен.
        """
        if request.url.path in app.unacceptable_paths:
            await blocklist_service.ban(
                client_ip,
                reason=f'Gateway > Unacceptable path: {request.url.path}'
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
            )

    async def __proxy_request(self, request: Request, app: App) -> StreamingResponse:
        """
        Передаем запрос к приложению.
        """
        response = await self.__client.request(
            method=request.method,
            url=f'{app.redirect_url}{request.url.path}',
            headers=request.headers,
            content=await request.body()
        )

        # Возврат ответа
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )


    async def process_request(self, request: Request):
        """
        Парсим запрос проверяем его корректность.
        Если все проверки пройдены отправляем запрос к приложению.
        """
        # Забираем заголовок app_redirect из nginx и ищем соответствующее приложение.
        # Если приложение не найдено, выбрасываем исключение 400
        app = self.__find_app(request)

        # Проверяем, что метод запроса допустим для данного приложения
        self.__check_allowed_method(request, app)

        # Получаем IP клиента
        client_ip = self.__get_client_ip(request)

        # Проверяем путь запроса
        await self.__check_unacceptable_path(request, app, client_ip)

        # Проверяем таймер
        self.__check_timer(app)

        # Запрашиваем из сервиса блокировок разрешен ли доступ к приложению
        # Если доступ запрещен, выбрасываем исключение 403
        if app.blocker_check and await blocklist_service.in_ban(client_ip, self.__redis):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied'
            )

        # Отправляем запрос к приложению
        await self.__proxy_request(request, app)
