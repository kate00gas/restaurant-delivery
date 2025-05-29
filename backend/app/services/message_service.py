




import aio_pika
import json
from typing import Optional, Any
from app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

class MessageService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.order_exchange: Optional[aio_pika.abc.AbstractExchange] = None

    async def connect(self):
        max_retries = 5
        retry_delay = 5 # seconds
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
                self.channel = await self.connection.channel()

                # Объявляем Exchange для событий заказов (topic для гибкой маршрутизации)
                self.order_exchange = await self.channel.declare_exchange(
                    settings.ORDER_EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
                )

                logger.info("Successfully connected to RabbitMQ and declared exchange.")


                self.order_queue = await self.channel.declare_queue(
                    "orders_queue",  # Имя очереди
                    durable=True,  # Сохранять при перезапуске
                    arguments={
                        'x-message-ttl': 86400000  # TTL 24 часа (опционально)
                    }
                )

                # Привяжите очередь к exchange
                await self.order_queue.bind(
                    self.order_exchange,
                    routing_key=settings.ORDER_CREATED_ROUTING_KEY
                )

                logger.info(f"Created and bound queue: {self.order_queue.name}")

                # Здесь можно объявить очереди и биндинги, если этот сервис будет и слушать
                # await self.setup_queues()
                return # Успешное подключение
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying connection in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Max connection retries reached. RabbitMQ connection failed.")
                    self.connection = None
                    self.channel = None
                    self.order_exchange = None
                    # Можно выбросить исключение или просто продолжить без RabbitMQ
                    # raise ConnectionError("Could not connect to RabbitMQ")

    async def disconnect(self):
        try:
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
                logger.info("RabbitMQ channel closed.")
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                logger.info("RabbitMQ connection closed.")
        except Exception as e:
             logger.error(f"Error during RabbitMQ disconnect: {e}")

    async def publish_message(self, exchange: aio_pika.abc.AbstractExchange, routing_key: str, message_body: Any):
        if not self.channel or self.channel.is_closed or not exchange:
            logger.error("Cannot publish message: RabbitMQ channel or exchange is not available.")
            return

        try:
            # Сериализуем сообщение в JSON
            body = json.dumps(message_body).encode()

            message = aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT # Делаем сообщение устойчивым к перезапуску брокера
            )

            await exchange.publish(message, routing_key=routing_key)
            logger.info(f"Published message to exchange '{exchange.name}' with routing key '{routing_key}'")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

    async def publish_order_created_event(self, order_data: dict):
        """Публикация события о создании заказа."""
        await self.publish_message(
            exchange=self.order_exchange,
            routing_key=settings.ORDER_CREATED_ROUTING_KEY,
            message_body=order_data
        )

# Создаем экземпляр сервиса
message_service = MessageService(settings.RABBITMQ_URL)





    # async def setup_queues(self):
    #     """Пример объявления очереди и биндинга (если нужно слушать)."""
    #     if not self.channel or not self.order_exchange: return
    #
    #     # Очередь для обработки подтверждений заказов (например)
    #     order_confirmation_queue = await self.channel.declare_queue(
    #         "order_confirmation_queue", durable=True
    #     )
    #     # Биндим очередь к exchange по ключу
    #     await order_confirmation_queue.bind(self.order_exchange, routing_key="order.created")
    #     logger.info("Declared and bound order_confirmation_queue")
    #
    #     # Начать слушать очередь
    #     # await order_confirmation_queue.consume(self.on_order_created_message)

    # async def on_order_created_message(self, message: aio_pika.abc.AbstractIncomingMessage):
    #     """Пример обработчика входящего сообщения."""
    #     async with message.process(): # Подтверждает получение сообщения после выполнения
    #         try:
    #             data = json.loads(message.body.decode())
    #             logger.info(f"Received order created message: {data}")
    #             # ... логика обработки ...
    #         except Exception as e:
    #             logger.error(f"Error processing message: {e}")
    #             # Можно добавить логику nack() для повторной обработки или dead-lettering

