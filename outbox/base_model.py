import datetime
import re
import uuid
from typing import TypeVar

from pydantic.alias_generators import to_camel
from sqlalchemy import UUID, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column
from typing_extensions import Annotated

_FACTORY_CLS = TypeVar("_FACTORY_CLS", bound="BaseModel")


def to_snake_case(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


uuid_pk = Annotated[
    uuid.UUID, mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
]
str_128 = Annotated[
    str,
    mapped_column(
        String(128),
        nullable=False,
    ),
]
date_time = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True)),
]
created_at = Annotated[
    datetime.datetime,
    mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now()),
]
updated_at = Annotated[
    datetime.datetime,
    mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    ),
]

str_500 = Annotated[
    str,
    mapped_column(
        String(500),
        nullable=False,
    ),
]


class BaseModel(DeclarativeBase):
    __abstract__ = True
    uuid: Mapped[uuid_pk]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    @declared_attr.directive
    def __tablename__(cls):
        return to_snake_case(cls.__name__)

    @classmethod
    def factory(cls: type, **kwargs) -> _FACTORY_CLS:
        return cls(**kwargs)

    def to_dict(self, camel_case: bool = False):
        if camel_case:
            return {to_camel(c.name): getattr(self, c.name) for c in self.__table__.columns}
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        return self



