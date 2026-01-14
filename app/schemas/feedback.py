from typing import Literal

from pydantic import BaseModel, field_validator

FeedBackType = Literal["suggestion", "text_for_admin", "review", "review_score"]


class FeedbackCreateSchema(BaseModel):
    """Схема для state_data - состояния памяти содержащее инфо с ОС клиента. Данные для сохранения в БД."""

    text: str
    feedback_type: str
    coffee_point_id: int | None = None
    photos: str | None = None
    user_id: int

class FeedbackFinalState(BaseModel):
    """Схема для state_data - состояния памяти, полная колекция с ОС клиента."""

    coffee_point_id: int
    bot_message_id: int
    feedback_type: Literal["suggestion", "review"]
    feedback_type_rus: str
    name: str
    text: str
    photos: str | None = None

    @field_validator("feedback_type", mode="before")
    @classmethod
    def validate_feedback_type(cls, v: str) -> str:
        """Валидирует и преобразует feedback_type."""
        if v == "review_score":
            return "review"
        elif v not in {"suggestion", "review"}:
            raise ValueError(f"feedback_type должен быть 'suggestion', 'review' или 'review_score', получено: {v}")
        return v
