from dataclasses import dataclass


@dataclass
class Client:
    host: str


@dataclass
class MockRequest:
    url: str = ''
    method: str = 'GET'
    headers: dict | None = None
    body: bytes | None = None
    client: Client | None = None


async def in_ban(*args, **kwargs) -> bool:
    return False


@dataclass
class ProxyRequest:
    method: str
    url: str
    headers: dict | None = None
    content: bytes | None = None


async def proxy_request(*args, **kwargs):
    return ProxyRequest(*args, **kwargs)
