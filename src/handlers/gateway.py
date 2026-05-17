import json
from dataclasses import dataclass

from fastapi import Request

from core.redis_client import RedisClient


@dataclass(frozen=True, slots=True)
class App:
    name: str
    redirect_url: str

    blocker_check: bool = True
    auth_only: bool = False

    max_rpm: int = 500


class GatewayHandler:
    __apps: dict[str, App] = {}

    def __init__(self, redis: RedisClient):
        self.__redis = redis
        self.__load_apps()

    def __load_apps(self):
        with open('apps.json') as f:
            data = json.load(f)
            for app in data:
                self.__apps[app['name']] = App(**app)

    def __find_app(self, request: Request) -> App | None:
        """
        Забираем app_redirect из заголовка njinx и ищем соответствующее приложение.
        """
        return self.__apps.get(request.headers.get('app_redirect', ''), None)

    def parse_request(self, request: Request):
        """
        Парсим запрос проверяем его корректность.
        Если все проверки пройдены отправляем запрос к приложению.
        """
        if
