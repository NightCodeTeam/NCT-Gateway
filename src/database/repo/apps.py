from sqlalchemy.ext.asyncio import AsyncSession

from core.sql_repository import RepositoryObj
from src.database.models.apps import App


class AppsRepo(RepositoryObj):
    def __init__(self, session: AsyncSession):
        super().__init__(App, session=session)

    async def exists(self, app_id: int) -> bool:
        return await self._exists(App.id == app_id)

    async def by_id(self, app_id: int, load_relations: bool = True) -> App | None:
        return await self.get(
            filter_=App.id == app_id,
            load_relations=load_relations,
        )

    async def new(self, app_id: int) -> bool:
        return await self.add(App(id=app_id))
