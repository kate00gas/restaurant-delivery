from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Определяем базовый класс для моделей SQLAlchemy
class Base(DeclarativeBase):
    # Можно определить общие настройки здесь, например, для именования таблиц/индексов
    metadata = MetaData()
    pass