from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from app import crud, schemas
from app.db.session import get_db
from app.services.message_service import message_service
from app.services.cache_service import cache_service
from app.api.dependencies import get_current_user_id

router = APIRouter()

@router.post("/", response_model=schemas.Order, status_code=201)
async def create_order(
    order_in: schemas.OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """
    Создать новый заказ.
    Отправляет сообщение в RabbitMQ после успешного создания.
    Инвалидирует кэш ресторана (т.к. доступность блюд могла проверяться).
    """
    try:
        restaurant = await crud.crud_restaurant.get_restaurant(db, order_in.restaurant_id)
        if not restaurant or not restaurant.is_active:
            raise HTTPException(status_code=404, detail=f"Restaurant with id {order_in.restaurant_id} not found or not active")
        created_order = await crud.crud_order.create_order(db=db, order_in=order_in, user_id=current_user_id)
        order_data_for_mq = schemas.Order.model_validate(created_order).model_dump(mode='json')
        await message_service.publish_order_created_event(order_data_for_mq)
        await cache_service.clear_cache_for_restaurant(str(order_in.restaurant_id))
        return created_order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while creating order")

@router.get("/", response_model=List[schemas.Order])
async def read_orders(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """
    Получить список заказов текущего пользователя.
    """
    orders = await crud.crud_order.get_orders_by_user(db=db, user_id=current_user_id, skip=skip, limit=limit)
    return orders

@router.get("/{order_id}", response_model=schemas.Order)
async def read_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id)
):
    """
    Получить детали конкретного заказа пользователя.
    """
    order = await crud.crud_order.get_order(db=db, order_id=order_id, user_id=current_user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found or you don't have access")
    return order