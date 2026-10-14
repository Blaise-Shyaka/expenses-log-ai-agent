from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Owns the request's transaction; repositories sharing the session only flush."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()
