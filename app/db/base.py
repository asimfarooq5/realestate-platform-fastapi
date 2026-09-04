from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from app.core.config import settings

# Use NullPool for SQLite (single-file, no pooling benefit),
# AsyncAdaptedQueuePool for PostgreSQL and other server databases.
if settings.DATABASE_URL.startswith("sqlite"):
    poolclass = NullPool
    pool_kwargs = {}
else:
    poolclass = AsyncAdaptedQueuePool
    pool_kwargs = {"pool_pre_ping": True}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=poolclass,
    **pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
