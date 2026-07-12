from uuid import uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.types import BINARY

from db.base_class import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(BINARY(16), index=True, primary_key=True, default=lambda: uuid4().bytes)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
