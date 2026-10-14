from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BINARY

from db.base_class import Base


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[bytes] = mapped_column(
        BINARY(16), index=True, primary_key=True, default=lambda: uuid4().bytes
    )
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
