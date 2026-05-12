import logging

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from .database import new_session


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with new_session() as session:
        try:
            session.begin()
            yield session
            await session.commit()
        except Exception as e:
            logging.error(e)
            await session.rollback()
            raise e
