import asyncio
import datetime

from aio_pika import ExchangeType
from dependency_injector.wiring import inject

from outbox.base_repo import BaseRepository, transactional
from outbox.logger import LOGGER
from outbox.model import OutBox, MessageStatus
from outbox.repo import OutBoxRepository
from outbox.rmq.rabbitmq import RabbitMQ
from outbox.rmq.schemas import SendMessageSchema, BindingSchema, ExchangeSchema


class OutBoxService:
    @inject
    def __init__(self,
                 base_repo: BaseRepository,
                 outbox_repo: OutBoxRepository,
                 publisher: RabbitMQ):
        self._base_repo = base_repo
        self._outbox_repo = outbox_repo
        self._publisher = publisher

    @property
    def base_repo(self):
        return self._base_repo

    @transactional(commit_at_end=False)
    async def get_last_100_pending(self) -> list[OutBox]:
        return await self._outbox_repo.get_last_100_pending()

    @transactional(commit_at_end=True)
    async def add_message(self, message: OutBox):
        return await self._outbox_repo.add_message(message)

    async def _send_to_rmq(self,
                           payload: dict,
                           routing_key: str,
                           exchange_name: str = "outbox",
                           queue_name: str = "outbox",
                           ):
        _message_to_send = SendMessageSchema(
            message=payload,
            binding=BindingSchema(
                route_key=routing_key,
                queue_name=queue_name,
                exchange=ExchangeSchema(
                    name=exchange_name,
                    type=ExchangeType.DIRECT
                ),
            )
        )
        await self._publisher.send_message(
            _message_to_send
        )

    @transactional(commit_at_end=True)
    async def _publish_message(self, message: OutBox):
        await self._send_to_rmq(message.data,
                                message.routing_key,
                                message.exchange_name,
                                message.queue_name)  # type: ignore
        await self._outbox_repo.update_message(message,
                                               {"status": MessageStatus.processed,
                                                "processed_on": datetime.datetime.utcnow()})

    async def publish_message(self):
        _messages = await self.get_last_100_pending()
        LOGGER.info(f"Publishing {len(_messages)} messages")
        _publisher_tasks = [
            asyncio.create_task(self._publish_message(_message))
            for _message in _messages
        ]

        await asyncio.gather(*_publisher_tasks)
