from core.redis_client import RedisClient


class GatewayHandler:
    def __init__(self, redis: RedisClient):
        self.__redis = redis
