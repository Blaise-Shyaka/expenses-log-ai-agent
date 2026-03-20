#standard packages
from uuid import uuid4

#third party packages
from sqlalchemy import  func, DateTime
from sqlalchemy.types import BINARY
from sqlalchemy.orm import mapped_column

#local packages
from db.base_class import Base


class BaseModel(Base):
    __abstract__ = True

    id = mapped_column(BINARY(16), index=True, primary_key=True, default=lambda: uuid4().bytes)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())