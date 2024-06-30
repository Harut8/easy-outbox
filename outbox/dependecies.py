import sys

from dependency_injector import providers, containers
from dependency_injector.containers import DeclarativeContainer
from outbox.base_repo import BaseRepository
from outbox.postgres import PostgresDB
from outbox.repo import OutBoxRepository
from outbox.rmq.rabbitmq import RabbitMQ
from outbox.scheduler import Scheduler
from outbox.service import OutBoxService
from outbox.settings import OutboxSettings


class DependencyContainer(DeclarativeContainer):
    config = OutboxSettings()
    rmq = providers.Singleton(
        RabbitMQ,
        url=config.RMQ_URL,
    )
    db = providers.Singleton(
        PostgresDB,
        url=config.POSTGRES_DSN,
    )
    base_repo = providers.Singleton(BaseRepository, db=db.provided.session)
    outbox_repo = providers.Singleton(
        OutBoxRepository,
        db=db
    )
    service = providers.Factory(
        OutBoxService,
        base_repo=base_repo,
        outbox_repo=outbox_repo,
        publisher=rmq
    )
    scheduler_app = providers.Singleton(
        Scheduler,
        db=db,
    )


container = DependencyContainer()
container.init_resources()
