import json

from aio_pika import IncomingMessage, connect
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractExchange,
    AbstractQueue,
)
from pydantic import AmqpDsn

from outbox.logger import LOGGER
from outbox.rmq.schemas import BindingSchema, SendMessageSchema


class RabbitMQ:
    logger = LOGGER

    def __init__(
        self,
        url: AmqpDsn,
    ):
        self._url = url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchanges: dict[str, AbstractExchange] = {}
        self._bindings: list[BindingSchema] = []
        self._processed_bindings: list[BindingSchema] = []
        self._queues: list[AbstractQueue] = []

    @property
    def connection(self) -> AbstractConnection:
        return self._connection

    @property
    def channel(self) -> AbstractChannel:
        return self._channel

    @property
    def exchanges(self) -> dict[str, AbstractExchange]:
        return self._exchanges

    @property
    def bindings(self) -> list[BindingSchema]:
        return self._bindings

    async def connect(self):
        self._connection = await connect(self._url)
        self._channel = await self._connection.channel()
        RabbitMQ.logger.info("Connected to RabbitMQ")

    async def add_binding(self, binding: BindingSchema):
        self._bindings.append(binding)

    async def declare_queue(self, queue_name):
        try:
            for _binding in self._bindings:
                if _binding.queue_name == queue_name:
                    _queue: AbstractQueue = await self.channel.declare_queue(
                        name=_binding.queue_name, durable=_binding.is_durable
                    )
                    if _binding.exchange.name not in self._exchanges:
                        self._exchanges[
                            _binding.exchange.name
                        ] = await self.channel.declare_exchange(
                            name=_binding.exchange.name,
                            type=_binding.exchange.type,
                            durable=_binding.exchange.is_durable,
                        )
                        self.logger.info(f"Declared exchange: {_binding.exchange.name}")
                    if _binding.exchange.need_bind and (_binding not in self._processed_bindings):
                        await _queue.bind(
                            exchange=self._exchanges[_binding.exchange.name],
                            routing_key=_binding.route_key,
                        )
                        self.bindings.remove(_binding)
                        self._processed_bindings.append(_binding)
                        self.logger.info(
                            f"Bound queue: {queue_name}"
                            f" to exchange: {_binding.exchange.name}"
                            f" with routing key: {_binding.route_key}"
                        )

            return _queue
        except Exception as e:
            self.logger.exception(e)

    async def send_message(self, message_schema: SendMessageSchema):
        if not self.channel or not self.connection:
            await self.connect()
        if self.channel.is_closed:
            self._channel = await self._connection.channel()
        if message_schema.binding:
            await self.add_binding(message_schema.binding)
            await self.declare_queue(message_schema.binding.queue_name)
        _exchange_name = message_schema.exchange_name or message_schema.binding.exchange.name
        _routing_key = message_schema.routing_key or message_schema.binding.route_key
        await self.exchanges[_exchange_name].publish(
            message_schema.message, _routing_key  # type: ignore
        )