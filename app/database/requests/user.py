from datetime import datetime
from typing import TypedDict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Drink, DrinkResult, Ingredient, IngredientResult, User
from app.database.requests.base import connection

DrinkType = type[Drink]


class UserDataHint(TypedDict):
    """Хинт для объекта с данными юзера."""

    tg_id: int
    tg_username: str | None
    first_name: str | None
    full_name: str | None
    last_name: str | None
    been_deleted: bool | None

class UserUpdateHint(TypedDict):
    """Данные юзера для обновления."""

    name: str
    update_dt: datetime


@connection
async def set_user(session: AsyncSession, user_data: UserDataHint) -> None:
    """Создаем пользователя при нажатии кнопки /start, его нет в БД.

    Args:
        session: асинхронная сессия движка sqlalchemy
        user_data (UserDataHint): параметры пользователя.
    """
    user = await session.scalar(select(User).where(User.tg_id == user_data["tg_id"]))
    if not user:
        session.add(User(**user_data))
        await session.commit()

@connection
async def get_drink(session: AsyncSession, item_id: str) -> DrinkResult:
    """Получаем напиток.

    Args:
        session: асинхронная сессия движка sqlalchemy
        item_id: значение хранящее id записи, например item_1
    """
    id_ = int(item_id.split("_")[-1])
    stmt = select(Drink).where(Drink.id == id_).options(
        selectinload(Drink.photos),
        selectinload(Drink.ingredients)
    )  # TODO: возможно можно еще как то сделать, что бы подгружались фото ингредиентов по связи.
    result = await session.execute(stmt)
    res = result.scalar_one_or_none()
    drink = res.drink_to_dict()
    return drink

@connection
async def get_igredient_photo(session: AsyncSession, item_id: str) -> IngredientResult:
    """Получаем ингредиент с фотографией благодаря relationship.

    Args:
        session: асинхронная сессия движка sqlalchemy
        item_id: значение хранящее id записи, например ingredient_item_3
    """
    id_ = int(item_id.split("_")[-1])
    stmt = select(Ingredient).where(Ingredient.id == id_).options(
        selectinload(Ingredient.photos),
    )
    result = await session.execute(stmt)
    res = result.scalar_one_or_none()
    return res.ingredient_to_dict()

@connection
async def update_user(session: AsyncSession, user_id: int, data: UserUpdateHint) -> None:
    """Обновление юзера.

    Args:
        session: асинхронная сессия движка sqlalchemy
        user_id: id пользователя. НЕ телеграм id
        data: новые параметры пользователя.
    """
    stmt = update(User).where(User.id == user_id).values(**data)
    await session.execute(stmt)
    await session.commit()

@connection
async def get_user_id(session: AsyncSession, tg_user_id: int) -> int:
    """Получаем id пользователя. Не телеграм id.

    Args:
        session (AsyncSession): асинхронная сессия движка sqlalchemy
        tg_user_id (int): телеграм id пользователя.
    """
    stmt = select(User.id).where(User.tg_id == tg_user_id)
    return await session.scalar(stmt)
