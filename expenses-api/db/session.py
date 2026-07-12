from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.db_config import app_settings

engine = create_async_engine(app_settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)
