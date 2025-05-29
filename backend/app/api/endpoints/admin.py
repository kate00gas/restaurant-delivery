from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.db.session import get_db
from app.services.cache_service import cache_service
from app.api.dependencies import get_current_admin
from typing import List
import uuid

router = APIRouter(tags=["Admin"])

@router.get("/orders/", response_model=List[schemas.Order])
async def read_orders(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Получить все заказы (для админа)"""
    return await crud.crud_order.admin_get_all_orders(db, skip=skip, limit=limit)

@router.get("/orders/{order_id}", response_model=schemas.Order)
async def read_order(
        order_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Получить детали конкретного заказа (для админа)"""
    order = await crud.crud_order.admin_get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.patch("/orders/{order_id}", response_model=schemas.Order)
async def update_order(
        order_id: uuid.UUID,
        order_in: schemas.OrderUpdate,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Обновить статус заказа"""
    return await crud.crud_order.admin_update_order_status(db, order_id, order_in.status)

@router.get("/restaurants/", response_model=List[schemas.Restaurant])
async def read_all_restaurants(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Получить все рестораны, включая неактивные (для админа)"""
    return await crud.crud_restaurant.get_all_restaurants(db, skip=skip, limit=limit)

@router.get("/restaurants/{restaurant_id}/menu/", response_model=List[schemas.MenuItem])
async def read_all_menu_items(
        restaurant_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Получить все пункты меню для ресторана, включая недоступные (для админа)"""
    return await crud.crud_restaurant.get_all_menu_items_by_restaurant(db, restaurant_id)

@router.post("/restaurants/", response_model=schemas.Restaurant)
async def create_restaurant(
        restaurant_in: schemas.RestaurantCreate,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Создать новый ресторан"""
    existing_restaurant = await crud.crud_restaurant.get_restaurant_by_name(db, restaurant_in.name)
    if existing_restaurant:
        raise HTTPException(status_code=400, detail="Restaurant with this name already exists")
    return await crud.crud_restaurant.create_restaurant(db, restaurant_in)

@router.delete("/restaurants/{restaurant_id}", status_code=204)
async def delete_restaurant(
        restaurant_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Delete a restaurant, its menu, and associated orders."""
    restaurant = await crud.crud_restaurant.get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    await crud.crud_restaurant.delete_restaurant(db, restaurant_id)
    await cache_service.clear_cache_for_restaurant(str(restaurant_id))

@router.post("/menu-items/", response_model=schemas.MenuItem)
async def create_menu_item(
        menu_item_in: schemas.MenuItemCreate,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Создать новый пункт меню"""
    menu_item = await crud.crud_restaurant.create_menu_item(db, menu_item_in)
    await cache_service.clear_cache_for_restaurant(str(menu_item_in.restaurant_id))
    return menu_item

@router.delete("/menu-items/{item_id}", status_code=204)
async def delete_menu_item(
        item_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Delete a menu item and clear the restaurant's cache."""
    restaurant_id = await crud.crud_restaurant.delete_menu_item(db, item_id)
    await cache_service.clear_cache_for_restaurant(str(restaurant_id))

@router.get("/order-statuses/", response_model=List[str])
async def get_order_statuses(current_admin: schemas.User = Depends(get_current_admin)):
    """Return all valid order statuses."""
    from app.models.order import OrderStatusEnum
    return [status.value for status in OrderStatusEnum]

@router.get("/users/", response_model=List[schemas.User])
async def read_all_users(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_admin: schemas.User = Depends(get_current_admin)
):
    """Получить всех пользователей (для админа)"""
    return await crud.crud_user.get_all_users(db, skip=skip, limit=limit)

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from app import crud, schemas, services
# from app.db.session import get_db
# import uuid
# from app.models.restaurant import MenuItem
# from sqlalchemy.future import select
#
# router = APIRouter(tags=["Admin"])
#
# @router.get("/orders/", response_model=list[schemas.Order])
# async def read_orders(
#     skip: int = 0,
#     limit: int = 100,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Получить все заказы (для админа)"""
#     return await crud.crud_order.admin_get_all_orders(db, skip=skip, limit=limit)
#
# @router.patch("/orders/{order_id}", response_model=schemas.Order)
# async def update_order(
#     order_id: uuid.UUID,
#     order_in: schemas.OrderUpdate,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Обновить статус заказа"""
#     order = await crud.crud_order.admin_update_order_status(db, order_id, order_in.status)
#     if not order:
#         raise HTTPException(status_code=404, detail="Order not found")
#     return order
#
# @router.delete("/restaurants/{restaurant_id}", status_code=204)
# async def delete_restaurant(
#     restaurant_id: uuid.UUID,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Удалить ресторан и его меню"""
#     restaurant = await crud.crud_restaurant.get_restaurant(db, restaurant_id)
#     if not restaurant:
#         raise HTTPException(status_code=404, detail="Restaurant not found")
#     await db.delete(restaurant)
#     await db.commit()
#     return None
#
# @router.delete("/menu-items/{item_id}", status_code=204)
# async def delete_menu_item(
#     item_id: uuid.UUID,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Delete a menu item and clear the restaurant's cache."""
#     restaurant_id = await crud.crud_restaurant.delete_menu_item(db, item_id)
#     # Clear the cache for the associated restaurant
#     await services.cache_service.clear_cache_for_restaurant(str(restaurant_id))