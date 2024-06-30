import functools
from typing import Callable, Coroutine, Generic, Sequence, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from outbox.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


def transactional(commit_at_end: bool = False):
    def __wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def _wrapper(self, *args, **kwargs):
            async with self.base_repo.db() as session:
                for _attr, _value in self.__dict__.items():
                    if _attr.endswith("_repo"):
                        _repo = getattr(self, _attr)
                        setattr(_repo, "session", session)
                try:
                    result = await func(self, *args, **kwargs)
                    if commit_at_end:
                        await session.commit()
                    return result
                except Exception as e:
                    await session.rollback()
                    raise e
                finally:
                    await session.close()

        return _wrapper

    return __wrapper


class BaseRepository(Generic[T]):
    def __init__(self, db: async_scoped_session):
        self._db: async_scoped_session = db
        self._session: AsyncSession | None = None

    @classmethod
    def factory(cls: type, **kwargs):
        return cls(**kwargs)

    @property
    def db(self):
        return self._db

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, session):
        self._session = session

    @staticmethod
    async def _insert_instance(instance: T, db: AsyncSession):
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

    async def run_select_stmt_for_one(self, stmt) -> T:
        result = await self.session.execute(stmt)
        return result.scalar()

    async def run_select_stmt_for_all(self, stmt) -> Sequence[T]:
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def insert_one_with_commit(self, instance: T):
        return await BaseRepository._insert_instance(instance, self._session)

    async def insert_one_without_commit(self, instance: T):
        self.session.add(instance)
        return instance

    async def insert_many_orm_with_commit(self, instances: list[T]) -> list[T]:
        self.session.add_all(instances)
        await self.session.commit()
        await self.session.refresh(instances)
        return instances

    async def insert_many_orm_without_commit(self, instances: list[T]) -> list[T]:
        self.session.add_all(instances)
        return instances

    async def bulk_insert_core_without_commit(self, instances: list[dict], mapping) -> list[dict]:
        await self.session.execute(
            mapping.__table__.insert(),
            instances,
        )
        return instances
