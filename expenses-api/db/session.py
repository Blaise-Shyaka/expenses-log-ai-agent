from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.db_config import app_settings


def make_session_factory(bind: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    # Responses are serialised after the unit of work commits. Expiring on commit would
    # make that serialisation lazy-load attributes, which needs IO an AsyncSession can't
    # do outside an await (MissingGreenlet).
    return async_sessionmaker(bind=bind, autoflush=False, expire_on_commit=False)


engine = create_async_engine(app_settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = make_session_factory(engine)
