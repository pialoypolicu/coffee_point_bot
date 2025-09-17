from typing import TypedDict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Drink, DrinkCoffeePointAssociation, Ingredient
from app.database.requests.base import connection

IngredientType = type[Ingredient]
DrinkType = type[Drink]
ModelType = Union[IngredientType, DrinkType]


class IngredientNamesHint(TypedDict):
    """Хинт с id и наименованиями ингридиентов."""

    id: int
    name: str


@connection
async def get_names(session: AsyncSession,
                    coffee_point_id: int) -> list[IngredientNamesHint]:
    """получаем названния ингридиентов.

    Args:
        session: асинхронная сессия движка sqlalchemy
        coffee_point_id: id кофе пойнта.
    """
    stmt = (
        select(Drink.id, Drink.name)
        .join(DrinkCoffeePointAssociation, Drink.id == DrinkCoffeePointAssociation.drink_id)
        .where(DrinkCoffeePointAssociation.coffee_point_id == coffee_point_id)
        .order_by(Drink.name)
    )
    result = await session.execute(stmt)
    return result.mappings().all()
