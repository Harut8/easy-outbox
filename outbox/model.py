from typing import Optional
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM, JSON

from outbox.base_model import BaseModel, date_time, str_128


class MessageStatus(Enum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


class OutBox(BaseModel):
    routing_key: Mapped[str_128]
    queue_name: Mapped[str_128]
    exchange_name: Mapped[str_128]
    data: Mapped[Optional[dict]] = mapped_column(type_=JSON)
    processed_on: Mapped[Optional[date_time]] = mapped_column(nullable=True)
    status = mapped_column(ENUM(MessageStatus), default=MessageStatus.pending)
