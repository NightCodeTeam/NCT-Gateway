from core.requests_makers import HttpMakerAsync
from core.redis_client import RedisClient

from src.settings import settings


class BlocklistServiceBase(HttpMakerAsync):
    """
    Базовый сервис блокировки IP-адресов. Используется только для тестов.
    """

    def __init__(self):
        super().__init__(
            base_url=settings.BLOCKER_URL,
            base_headers={
                'X-Access-Code': settings.BLOCKER_ACCESS_CODE
            },
            parse_method=self._get_simple_response,
        )

    async def in_ban(self, ip: str, redis: RedisClient) -> bool:
        print(f'{self.__class__.__name__} > in_ban({ip})')
        return False

    async def ban(
        self, ip: str,
        reason: str = 'no reason',
        duration_days: int = 3,
        permanent: bool = False,
        white: bool = False
    ) -> bool:
        """
        Блокировка IP-адреса.
        """
        print(f'{self.__class__.__name__} > ban({ip}, reason={reason}, duration_days={duration_days}, permanent={permanent}, white={white})')
        return True


class BlocklistService(BlocklistServiceBase):
    """
    Сервис блокировки IP-адресов.
    """

    def __init__(self):
        super().__init__()

    async def in_ban(self, ip: str, redis: RedisClient) -> bool:
        data = await self.redis_cache(
            key=f'in_ban:ip_address:{ip}',
            spec_app_prefix=settings.BLOCKER_REDIS_PREFIX,
            redis=redis
        )
        if data is not None and type(data.get('ok')) == bool:
            return data['ok']
        return (await self._make(f'/v1/bans/{ip}', method='GET')).json.get('ok', False)

    async def ban(
        self, ip: str,
        reason: str = 'no reason',
        duration_days: int = 3,
        permanent: bool = False,
        white: bool = False
    ) -> bool:
        return (await self._make(f'/v1/bans', method='POST', json={
            'ip': ip,
            'reason': reason,
            'duration_days': duration_days,
            'permanent': permanent,
            'white': white
        })).json.get('ok', False)


blocklist_service = BlocklistService()
