

# ББББББ


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from decimal import Decimal
from fastapi import HTTPException

from app.models.order import Order, OrderItem, OrderStatusEnum
from app.models.restaurant import MenuItem # Нужен для получения цены
from app.schemas.order import OrderCreate, OrderItemCreate, OrderUpdate

async def get_order(db: AsyncSession, order_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Order]:
    """Получить заказ по ID, проверяя владельца."""
    stmt = select(Order).where(Order.order_id == order_id, Order.user_id == user_id).options(
        selectinload(Order.items).selectinload(OrderItem.menu_item),
        selectinload(Order.restaurant)  # Load restaurant
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_orders_by_user(db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Order]:
    """Получить список заказов пользователя."""
    stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()).offset(skip).limit(limit).options(
        selectinload(Order.items),
        selectinload(Order.restaurant)  # Load restaurant
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_order(db: AsyncSession, order_in: OrderCreate, user_id: uuid.UUID) -> Order:
    """Создать новый заказ."""
    total_amount = Decimal(0)
    order_items_data = []
    item_ids = [item.item_id for item in order_in.items]

    # 1. Получаем актуальные цены для выбранных блюд из БД одним запросом
    menu_items_stmt = select(MenuItem).where(
        MenuItem.item_id.in_(item_ids),
        MenuItem.restaurant_id == order_in.restaurant_id, # Убедимся, что блюда из нужного ресторана
        MenuItem.is_available == True # И что они доступны
    )
    menu_items_result = await db.execute(menu_items_stmt)
    menu_items_dict = {item.item_id: item for item in menu_items_result.scalars().all()}

    # 2. Проверяем наличие всех блюд и считаем сумму
    if len(menu_items_dict) != len(item_ids):
        # Найти отсутствующие или недоступные ID
        missing_ids = set(item_ids) - set(menu_items_dict.keys())
        raise ValueError(f"Одно или несколько блюд недоступны или не найдены: {missing_ids}")

    for item_in in order_in.items:
        menu_item = menu_items_dict.get(item_in.item_id)
        if not menu_item: # Дополнительная проверка (не должна сработать из-за проверки выше)
             raise ValueError(f"Блюдо с ID {item_in.item_id} не найдено или недоступно.")

        item_total = menu_item.price * item_in.quantity
        total_amount += item_total
        order_items_data.append({
            "item_id": item_in.item_id,
            "quantity": item_in.quantity,
            "price_per_item": menu_item.price # Цена из БД на момент заказа
        })

    # 3. Создаем объект заказа
    db_order = Order(
        user_id=user_id,
        restaurant_id=order_in.restaurant_id,
        delivery_address=order_in.delivery_address,
        total_amount=total_amount,
        status=OrderStatusEnum.pending_confirmation # Начальный статус
    )
    db.add(db_order)
    await db.flush() # Получаем order_id перед созданием order_items

    # 4. Создаем объекты элементов заказа
    db_order_items = [OrderItem(**item_data, order_id=db_order.order_id) for item_data in order_items_data]
    db.add_all(db_order_items)

    # 5. Коммитим транзакцию
    await db.commit()
    await db.refresh(db_order, attribute_names=["items"]) # Обновляем заказ с загруженными items

    return db_order


# Административные функции (для admin.py)
async def admin_get_order(db: AsyncSession, order_id: uuid.UUID) -> Optional[Order]:
    """Получить любой заказ (для админа)."""
    stmt = select(Order).where(
        Order.order_id == order_id
    ).options(
        selectinload(Order.items).selectinload(OrderItem.menu_item),
        selectinload(Order.restaurant)  # Load restaurant
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def admin_get_all_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Order]:
    """Получить все заказы (для админа)."""
    stmt = select(Order).order_by(
        Order.created_at.desc()
    ).offset(skip).limit(limit).options(
        selectinload(Order.items),
        selectinload(Order.restaurant)  # Add restaurant loading
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def admin_update_order_status(
        db: AsyncSession,
        order_id: uuid.UUID,
        new_status: OrderStatusEnum
) -> Order:
    """Обновить статус заказа (для админа)."""
    order = await admin_get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order


async def admin_cancel_order(db: AsyncSession, order_id: uuid.UUID) -> Order:
    """Отменить заказ (для админа)."""
    return await admin_update_order_status(
        db, order_id, OrderStatusEnum.cancelled
    )