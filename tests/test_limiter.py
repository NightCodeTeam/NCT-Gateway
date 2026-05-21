import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from src.gateway.limiter import TokenBucket



def test_init(token_bucket: TokenBucket):
    """Test initialization of TokenBucket."""
    assert token_bucket.rate == 10
    assert token_bucket._TokenBucket__burst == 10
    assert token_bucket.tokens == 10
    # last_update is set to time.monotonic() upon initialization
    assert token_bucket._TokenBucket__last_update is not None


def test_consume_success(token_bucket: TokenBucket):
    """Test successful token consumption."""
    # Consume 5 tokens
    assert token_bucket.consume() is True
    assert token_bucket.tokens == 9

    # Consume remaining tokens
    assert token_bucket.consume(2) is True
    assert token_bucket.tokens == 7


def test_consume_failure(token_bucket: TokenBucket):
    """Test failed token consumption when tokens are insufficient."""
    # Consume all tokens
    token_bucket.consume(10)
    # Try to consume more
    assert token_bucket.consume(1) is False
    assert token_bucket.tokens == 0
