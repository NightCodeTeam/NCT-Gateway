import time


class TokenBucket:
    """Алгоритм Token Bucket - минимальное потребление CPU"""

    def __init__(self, rate: float, burst: int | None = None):
        """
        rate: количество запросов в секунду
        burst: максимальный всплеск (по умолчанию равен rate)
        """
        self.rate = rate
        self.burst = burst or rate
        self.tokens = self.burst
        self.last_update = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        """Пытается потребить токены. Возвращает True если успешно"""
        now = time.monotonic()

        # Пополняем токены
        elapsed = now - self.last_update
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_update = now

        # Потребляем
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_and_consume(self, tokens: int = 1) -> float:
        """Ждет и потребляет токены. Возвращает время ожидания"""
        while not self.consume(tokens):
            time.sleep(0.1 / self.rate)
        return 0.0
