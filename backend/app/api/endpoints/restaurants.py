
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app import crud, schemas, models
from app.db.session import get_db
from app.services.cache_service import cache_service # Импортируем сервис кэша

router = APIRouter(tags=["Admin"])

@router.get("/", response_model=List[schemas.Restaurant])
async def read_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список активных ресторанов.
    Кэширование здесь может быть сложным из-за пагинации,
    можно кэшировать весь список или отдельные страницы, но для простоты опустим.
    """
    restaurants = await crud.crud_restaurant.get_restaurants(db=db, skip=skip, limit=limit)
    return restaurants

@router.get("/{restaurant_id}", response_model=schemas.RestaurantWithMenu)
async def read_restaurant_with_menu(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"restaurant:{restaurant_id}:menu"
    cached_data = await cache_service.get(cache_key)

    if cached_data:
        try:
            return schemas.RestaurantWithMenu.model_validate(cached_data)
        except Exception as e:
            print(f"Cache data invalid for {cache_key}: {e}")

    db_restaurant = await crud.crud_restaurant.get_restaurant(db=db, restaurant_id=restaurant_id)
    if db_restaurant is None or not db_restaurant.is_active:
        raise HTTPException(status_code=404, detail="Restaurant not found or not active")

    schema_restaurant = schemas.RestaurantWithMenu.model_validate(db_restaurant)
    await cache_service.set(cache_key, schema_restaurant.model_dump(mode='json'))
    return schema_restaurant


@router.delete("/restaurants/{restaurant_id}", status_code=204)
async def delete_restaurant(
        restaurant_id: uuid.UUID,
        db: AsyncSession = Depends(get_db)
):
    """Delete a restaurant, its menu, and associated orders."""
    restaurant = await crud.crud_restaurant.get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Delete the restaurant (and cascade to menu items and orders)
    await crud.crud_restaurant.delete_restaurant(db, restaurant_id)

    # Clear the cache for this restaurant
    await cache_service.clear_cache_for_restaurant(str(restaurant_id))


# Эндпоинт для получения только меню (можно добавить при необходимости)
# @router.get("/{restaurant_id}/menu", response_model=List[schemas.MenuItem])
# async def read_restaurant_menu(
#     restaurant_id: uuid.UUID,
#     db: AsyncSession = Depends(get_db),
# ):
#     """Получить только доступное меню ресторана."""
#     # ... (логика с кэшированием, похожая на read_restaurant_with_menu)
#     menu_items = await crud.crud_restaurant.get_menu_items_by_restaurant(db=db, restaurant_id=restaurant_id)
#     if not menu_items:
#          # Проверить, существует ли сам ресторан, чтобы вернуть 404 если нужно
#          pass
#     return menu_items