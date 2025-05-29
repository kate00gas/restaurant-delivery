

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from app.core.config import settings

# Создаем асинхронный движок SQLAlchemy
# pool_pre_ping=True проверяет соединение перед использованием
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False) # echo=True для логгирования SQL

# Создаем фабрику асинхронных сессий
# expire_on_commit=False важно для FastAPI, чтобы объекты были доступны после коммита
AsyncSessionFactory = async_sessionmaker(
    engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function для получения сессии базы данных.
    Использует 'yield' для управления жизненным циклом сессии.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Коммит не нужен здесь, если операции CRUD делают коммит сами
            # await session.commit() # Раскомментируйте, если нужен автоматический коммит в конце запроса
        except Exception:
            await session.rollback()
            raise
        finally:
            # Закрытие сессии происходит автоматически при выходе из 'async with'
             pass # await session.close() - не требуется с async_sessionmaker


