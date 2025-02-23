from typing import TypedDict, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Drink, Ingredient
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
                    model: ModelType = Ingredient,
                    without_ids: list[int] | None = None) -> list[IngredientNamesHint]:
    """получаем названния ингридиентов.

    Args:
        session: асинхронная сессия движка sqlalchemy
        model: класс ORM модели.
        without_ids: список id записей, которые нужно исключить из выборки.
    """
    stmt = select(model.id, model.name)
    if without_ids:
        stmt = stmt.where(model.id.not_in(without_ids))
    result = await session.execute(stmt)
    return result.mappings().all()
