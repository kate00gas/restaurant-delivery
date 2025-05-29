


import uuid
from sqlalchemy import Column, String, Text, Boolean, Numeric, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import UUID # Используем UUID PostgreSQL
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    restaurant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    address = Column(String(500), nullable=False)
    phone_number = Column(String(50))
    email = Column(String(255), index=True)
    is_active = Column(Boolean, default=True)
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Связь один-ко-многим с MenuItems
    # lazy='selectin' - оптимальная стратегия загрузки для async
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan", lazy="selectin")


class MenuItem(Base):
    __tablename__ = "menu_items"
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.restaurant_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), index=True)
    is_available = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    # Связь многие-к-одному с Restaurant
    restaurant = relationship("Restaurant", back_populates="menu_items", lazy="joined") # joined для автоматической подгрузки ресторана
    # Индекс для внешнего ключа (хотя Alembic может создавать автоматически)
    __table_args__ = (Index('idx_menu_items_restaurant_id', 'restaurant_id'),)


