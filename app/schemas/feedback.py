from typing import Literal

from pydantic import BaseModel


class FeedbackCreateSchema(BaseModel):
    """Схема для state_data - состояния памяти содержащее инфо с ОС клиента. Данные для сохранения в БД."""

    text: str
    feedback_type: str
    coffee_point_id: int | None = None
    photos: list[str] | None = []
    user_id: int

class FeedbackFinalState(BaseModel):
    """Схема для state_data - состояния памяти, полная колекция с ОС клиента."""

    coffee_point_id: int
    bot_message_id: int
    feedback_type: Literal["suggestion", "review"]
    feedback_type_rus: str
    name: str
    text: str
    photo: str | None = None
