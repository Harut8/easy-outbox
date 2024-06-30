from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore
from apscheduler.eventbrokers.asyncpg import AsyncpgEventBroker
from apscheduler.triggers.interval import IntervalTrigger

from outbox.postgres import PostgresDB
from outbox.model import OutBox


class Scheduler:
    def __init__(self,
                 db: PostgresDB):
        self._db = db
        self._is_initialized = False
        self._data_store = None
        self._event_broker = None
        self._scheduler = None

    async def initialize(self):
        async with self._db.engine.begin() as session:
            await session.run_sync(OutBox.metadata.create_all)
        self._data_store = SQLAlchemyDataStore(self._db.engine)
        self._event_broker = AsyncpgEventBroker.from_async_sqla_engine(self._db.engine)
        self._is_initialized = True

    async def __aenter__(self):
        if not self._is_initialized:
            await self.initialize()
        if self._scheduler is None:
            self._scheduler = AsyncScheduler(self._data_store, self._event_broker)
        return self._scheduler

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._scheduler.__aexit__(exc_type, exc_val, exc_tb)
