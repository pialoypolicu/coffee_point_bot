from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    CoffeePoint,
    Drink,
    DrinkCoffeePointAssociation,
    DrinkResult,
    Ingredient,
    IngredientResult,
    User,
)
from app.database.requests.base import connection
from app.database.requests.keyboards import IngredientNamesHint

DrinkType = type[Drink]


class CoffeePointHint(TypedDict):
    """Хинт для кофейной точки."""

    id: int
    name: str
    address: str
    metro_station: str | None


class UserDataHint(TypedDict):
    """Хинт для объекта с данными юзера."""

    tg_id: int
    tg_username: str | None
    first_name: str | None
    full_name: str | None
    last_name: str | None
    been_deleted: bool | None


class UserContext:
    """класс с логикой при взаимодействии клиента с ботом."""

    @staticmethod
    @connection
    async def get_coffee_points_db(session: AsyncSession) -> list[CoffeePointHint]:
        """Получает список всех активных кофейных точек."""
        stmt = select(CoffeePoint).where(CoffeePoint.is_active.is_(True)).order_by(CoffeePoint.name)
        result = await session.execute(stmt)
        points = result.scalars().all()

        return [point.to_dict() for point in points]

    @staticmethod
    @connection
    async def get_coffee_point_info_db(session: AsyncSession, point_id: int) -> CoffeePointHint | None:
        """выборка карточки/параметров кофейной точки.

        Args:
            session: Асинхронная сессия БД
            point_id: ID кофейной точки.
        """
        stmt = select(CoffeePoint).where(CoffeePoint.id == point_id).where(CoffeePoint.is_active.is_(True))
        result = await session.execute(stmt)

        point = result.scalar_one_or_none()
        if point:
            return point.to_dict()
        return point

    @staticmethod
    @connection
    async def get_user(session: AsyncSession, user_id: int) -> User | None:
        """Получаем юзера из БД.

        Args:
            session: Асинхронная сессия БД
            user_id: ID пользователя телеграм
        """
        return await session.scalar(select(User).where(User.tg_id == user_id))

    @staticmethod
    @connection
    async def set_user_to_db(session: AsyncSession, user_data: UserDataHint) -> None:
        """Создаем пользователя при нажатии кнопки /start, его нет в БД.

        Args:
            session: асинхронная сессия движка sqlalchemy
            user_data (UserDataHint): параметры пользователя.
        """
        session.add(User(**user_data))
        await session.commit()

    @staticmethod
    @connection
    async def get_drink_detail_db(session: AsyncSession, item_id: str) -> DrinkResult:
        """Получаем напиток.

        Args:
            session: асинхронная сессия движка sqlalchemy
            item_id: значение хранящее id записи, например item_1
        """
        stmt = select(Drink).where(Drink.id == item_id).options(
            selectinload(Drink.photos),
            selectinload(Drink.ingredients)
        )
        result = await session.execute(stmt)
        res = result.scalar_one_or_none()
        drink = res.drink_to_dict()
        return drink

    @staticmethod
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

    @staticmethod
    @connection
    async def get_names_db(session: AsyncSession,
                           coffee_point_id: int) -> list[IngredientNamesHint]:
        """получаем названния напитков.

        Args:
            session: асинхронная сессия движка sqlalchemy
            coffee_point_id: ID кофейной точки.
        """
        stmt = (
            select(Drink.id, Drink.name)
            .join(DrinkCoffeePointAssociation, Drink.id == DrinkCoffeePointAssociation.drink_id)
            .where(DrinkCoffeePointAssociation.coffee_point_id == coffee_point_id)
            .order_by(Drink.name)
        )
        result = await session.execute(stmt)
        return result.mappings().all()
