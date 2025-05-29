import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, TIMESTAMP, func, Index, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

# Используем Python Enum для статусов заказа
class OrderStatusEnum(str, enum.Enum):
    pending_confirmation = "pending_confirmation"  # Нижний регистр
    confirmed = "confirmed"
    preparing = "preparing"
    ready_for_pickup = "ready_for_pickup"
    delivered = "delivered"
    cancelled = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True) # ID пользователя
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(SQLEnum(OrderStatusEnum, name="order_status", create_type=False), nullable=False, default=OrderStatusEnum.pending_confirmation, index=True) # Используем Enum
    total_amount = Column(Numeric(10, 2), nullable=False)
    delivery_address = Column(String(500), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связь с рестораном
    restaurant = relationship("Restaurant", lazy="joined")
    # Связь с элементами заказа
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.item_id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_per_item = Column(Numeric(10, 2), nullable=False) # Цена на момент заказа

    # Связь с заказом
    order = relationship("Order", back_populates="items", lazy="joined")
    # Связь с блюдом (можно добавить, если нужна информация о блюде прямо из OrderItem)
    menu_item = relationship("MenuItem", lazy="joined")