from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserDB


async def ensure_user(db: AsyncSession, user_uuid_str: str) -> None:
    user_uuid = UUID(user_uuid_str)
    user_id_bytes = user_uuid.bytes
    result = await db.execute(select(UserDB).where(UserDB.id == user_id_bytes))
    if result.scalars().first() is None:
        db.add(UserDB(id=user_id_bytes))
        await db.commit()
