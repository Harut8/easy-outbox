from asyncio import current_task
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)


class PostgresDB:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url, echo=echo, pool_size=5, max_overflow=10, future=True
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_async_scoped_session(self):
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )
        return session

    async def session_dependency(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session
            await session.close()

    async def scoped_session_dependency(self) -> AsyncSession:
        session = self.get_async_scoped_session()
        async with session() as session:
            print(session.bind.pool.status())
            yield session
            await session.close()

    @asynccontextmanager
    async def session(self) -> AsyncSession:
        try:
            async with self.session_factory() as session:
                print(session.bind.pool.status())
                yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
