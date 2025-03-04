from typing import TypedDict
from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.keyboards import create_main_keyboard
from app.logic.feedback import FEEDBACK_TYPES, FINAL_FEEDBACK_MSG, LogicFeedback


class LogicFeedbackData(TypedDict):
    state: AsyncMock
    message: AsyncMock
    expected_final_msg: str
    logic_feedback: AsyncMock


@pytest.fixture(params=["photo_file_id", None])
def logic_feedback_data(request: pytest.FixtureRequest,
                        mock_state: AsyncMock,
                        mock_logic_feedback: AsyncMock,
                        mock_message: AsyncMock) -> LogicFeedbackData:
    """Фикстура подготавливает динамические данные.

    Отрабатывает два кейса. когда клиент отправляет фото и ккогда не отправляет.

    Args:
        request: параметризация теста.
        mock_state: состояние памяти.
        mock_logic_feedback: логика работы с отзывами.
        mock_message: сообщение клиента.
    """
    photo = request.param
    name = "Иван"
    feedback_type = "suggestion"
    text = "Отличный бот!"
    feedback_type_rus = FEEDBACK_TYPES[feedback_type]
    final_feedback_msg = FINAL_FEEDBACK_MSG.format(name=name, feedback_type=feedback_type_rus, text=text)
    if photo:
        final_feedback_msg += "Фото: Загружено\n\n"
    else:
        final_feedback_msg += "Фото: Не загружено\n\n"
    final_feedback_msg += r"*Спасибо за обратную связь\!*"

    mock_logic_feedback.get_user_id.return_value = 123

    mock_state.get_data.return_value = {
        "name": name,
        "feedback_type": feedback_type,
        "text": "Отличный бот!",
        "photo": photo,
    }
    mock_message.from_user.id = 123
    return {"state": mock_state,
            "message": mock_message,
            "expected_final_msg": final_feedback_msg,
            "logic_feedback": mock_logic_feedback}

@pytest.fixture()
def main_keyboard() -> InlineKeyboardMarkup:
    """возвращает индайн клавиатуру с главной менюшкой."""
    return create_main_keyboard(False)
