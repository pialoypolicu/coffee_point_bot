from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Drink, Ingredient, Photo
from app.database.requests.base import connection


class IngredientHint(TypedDict):
    """Хинт создания игредиента."""
    postition_type: str
    name: str
    description: str
    photo: str

class DrinkHint(IngredientHint):
    """Хинт для создания карточки напитка с ингредиентами"""
    ingredient_id: str
    ingredient_ids: list[int]


@connection
async def set_ingredient(session: AsyncSession, data: IngredientHint) -> None:
    """Записываем ингредиент в БД.

    Args:
        data: параметры игредиента.
        session: асинхронная сессия движка sqlalchemy
    """
    ingredient = Ingredient(name=data["name"], description=data["description"])

    # Создание фото для ингредиента
    Photo(photo_string=data["photo"], ingredient=ingredient)
    session.add(ingredient)
    await session.commit()

@connection
async def set_drink(session: AsyncSession, data: DrinkHint) -> None:
    """Записываем напиток в БД.

    Args:
        session: асинхронная сессия движка sqlalchemy
        data: параметры напитка.
    """
    drink = Drink(name=data["name"], description=data["description"])
    # Создание фото для напиткка
    Photo(photo_string=data["photo"], drink=drink)
    ingredients = []
    for i in data["ingredient_ids"]:
        ingredient = await session.get(Ingredient, i)
        ingredients.append(ingredient)
    drink.ingredients.extend(ingredients)
    session.add(drink)
    await session.commit()
