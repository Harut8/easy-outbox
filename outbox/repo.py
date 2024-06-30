from typing import cast

from sqlalchemy import select

from outbox.base_repo import BaseRepository
from outbox.model import OutBox, MessageStatus


class OutBoxRepository(BaseRepository[OutBox]):

    async def get_last_100_pending(self) -> list[OutBox]:
        _stmt = (((select(OutBox)
                   .filter(OutBox.status == MessageStatus.pending))
                  .order_by(OutBox.created_at.desc()))
                 .limit(100))

        _messages = await self.run_select_stmt_for_all(_stmt)
        return cast(list[OutBox], _messages)

    async def add_message(self, message: OutBox):
        return await self.insert_one_without_commit(message)

    async def update_message(self, message: OutBox, payload: dict):
        message.update(**payload)
        return await self.insert_one_without_commit(message)
