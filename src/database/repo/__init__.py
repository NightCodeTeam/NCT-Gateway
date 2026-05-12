from sqlalchemy.ext.asyncio import AsyncSession

from .apps import AppsRepo
from core.sql_repository import DataBaseRepo


class DataBase(DataBaseRepo):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.apps = AppsRepo(session=session)


__all__ = (
    'DataBase',
)
