from datetime import datetime
from typing import TypedDict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CoffeePointExternalLink, FeedBack, Photo, User
from app.database.requests.base import connection
from app.schemas.feedback import FeedbackCreateSchema


class UserUpdateHint(TypedDict):
    """Данные юзера для обновления."""

    name: str
    update_dt: datetime


class FeedbackContext:
    """Класс для взаимодействия с БД."""

    @staticmethod
    @connection
    async def create_feedback(session: AsyncSession, data: FeedbackCreateSchema) -> None:
        """создаем отзыв/предложение клиента.

        Args:
            session: асинхронная сессия движка sqlalchemy
            data: словарь содержит значения отзыва/предложения.
        """
        feedback = FeedBack(**data.model_dump(exclude={"photos"}))
        if photo := data.photos:
            Photo(photo_string=photo, feedback=feedback)

        session.add(feedback)
        await session.commit()

    @staticmethod
    @connection
    async def get_user_id(session: AsyncSession, tg_user_id: int) -> int:
        """Получаем id пользователя. Не телеграм id.

        Args:
            session (AsyncSession): асинхронная сессия движка sqlalchemy
            tg_user_id (int): телеграм id пользователя.
        """
        stmt = select(User.id).where(User.tg_id == tg_user_id)
        return await session.scalar(stmt)

    # TODO: рассмотреть вариант ленивой выборки из модели CoffeePoint, связи один ко многим.
    @staticmethod
    @connection
    async def get_feedback_link(session: AsyncSession, coffee_point_id: int) -> CoffeePointExternalLink | None:
        """Получает активную внешнюю ссылку для отзывов о кофейне.

        Args:
            session: Асинхронная сессия SQLAlchemy
            coffee_point_id: ID кофейной точки
        """
        stmt = (
            select(CoffeePointExternalLink.url)
            .where(
                CoffeePointExternalLink.coffee_point_id == coffee_point_id,
                CoffeePointExternalLink.is_active.is_(True)
            )
            .order_by(CoffeePointExternalLink.id)  # или другой критерий сортировки
            .limit(1)
        )
        return await session.scalar(stmt)

    @staticmethod
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
