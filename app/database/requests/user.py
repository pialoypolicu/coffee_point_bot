from typing import TypedDict

from sqlalchemy import select
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
