from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import FeedBack, Photo
from app.database.requests.base import connection


@connection
async def create_feedback(session: AsyncSession, data: dict[str, str | int]):
    """создаем отзыв/предложение клиента.

    Args:
        session: асинхронная сессия движка sqlalchemy
    """
    feedback = FeedBack(text=data["text"], feedback_type=data["feedback_type"], user_id=data["user_id"])
    Photo(photo_string=data["photo"], feedback=feedback)
    # User(user=feedback)

    session.add(feedback)
    await session.commit()
