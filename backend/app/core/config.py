import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Restaurant Delivery API"
    API_V1_STR: str = "/api/v1"

    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/restaurant_db")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    ORDER_EXCHANGE_NAME: str = "order_events"
    ORDER_CREATED_ROUTING_KEY: str = "order.created"

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        pass

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()