from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, update
from typing import List, Optional
import uuid
from fastapi import HTTPException

from app.models.restaurant import Restaurant, MenuItem
from app.models.order import Order
from app.schemas.restaurant import RestaurantCreate, MenuItemCreate

async def get_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> Optional[Restaurant]:
    """Получить ресторан по ID с подгрузкой меню."""
    stmt = select(Restaurant).where(Restaurant.restaurant_id == restaurant_id).options(selectinload(Restaurant.menu_items))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_restaurant_by_name(db: AsyncSession, name: str) -> Optional[Restaurant]:
    """Получить ресторан по имени."""
    stmt = select(Restaurant).where(Restaurant.name == name).options(selectinload(Restaurant.menu_items))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def get_restaurants(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Restaurant]:
    """Получить список активных ресторанов (для клиентов)."""
    stmt = select(Restaurant).where(Restaurant.is_active == True).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_restaurants(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Restaurant]:
    """Получить все рестораны, включая неактивные (для админа)."""
    stmt = select(Restaurant).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_menu_items_by_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> List[MenuItem]:
    """Получить все доступные пункты меню для ресторана (для клиентов)."""
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id, MenuItem.is_available == True)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_all_menu_items_by_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> List[MenuItem]:
    """Получить все пункты меню для ресторана, включая недоступные (для админа)."""
    stmt = select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_restaurant(db: AsyncSession, restaurant_in: RestaurantCreate) -> Restaurant:
    """Создать новый ресторан."""
    db_restaurant = Restaurant(**restaurant_in.dict())
    db.add(db_restaurant)
    await db.commit()
    await db.refresh(db_restaurant)
    return db_restaurant

async def create_menu_item(db: AsyncSession, menu_item_in: MenuItemCreate) -> MenuItem:
    """Создать новый пункт меню и активировать ресторан."""
    restaurant = await get_restaurant(db, menu_item_in.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    db_menu_item = MenuItem(**menu_item_in.dict())
    db.add(db_menu_item)
    await db.flush()

    if not restaurant.is_active:
        await db.execute(
            update(Restaurant)
            .where(Restaurant.restaurant_id == menu_item_in.restaurant_id)
            .values(is_active=True)
        )

    await db.commit()
    await db.refresh(db_menu_item)
    return db_menu_item

async def delete_restaurant(db: AsyncSession, restaurant_id: uuid.UUID):
    """Delete a restaurant, its menu items, and associated orders."""
    await db.execute(
        delete(Order).where(Order.restaurant_id == restaurant_id)
    )
    await db.execute(
        delete(Restaurant).where(Restaurant.restaurant_id == restaurant_id)
    )
    await db.commit()

async def delete_menu_item(db: AsyncSession, item_id: uuid.UUID):
    """Delete a menu item by ID."""
    stmt = select(MenuItem).where(MenuItem.item_id == item_id)
    result = await db.execute(stmt)
    menu_item = result.scalar_one_or_none()

    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    restaurant_id = menu_item.restaurant_id
    await db.execute(
        delete(MenuItem).where(MenuItem.item_id == item_id)
    )
    await db.commit()

    return restaurant_id