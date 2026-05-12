from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    url=settings.DB_PATH,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)
new_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        #await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
