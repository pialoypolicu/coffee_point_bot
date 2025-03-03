from typing import TypedDict
from unittest.mock import AsyncMock

import pytest
from aiogram.types import CallbackQuery, Message

from app.handlers.feedback import ANSWER_MSG, FEEDBACK_STEPS_MSG, FEEDBACK_TYPES, NAME_FORM_MSG


class FeedbackData(TypedDict):
    """Хинт колбека и ожидаемых значений для теста."""

    callback: AsyncMock
    expected_msg: str
    expected_fb_type: str
    expected_answer_msg: str
    expected_feedback_type_rus: str

class FeedbackTextData(TypedDict):
    """Хинт сообщения и ожидаемых значений для теста."""

    message: AsyncMock
    expected_text: str

class FeedbackNameForm(FeedbackTextData):
    """Хинт сообщения, состояния памяти и ожидаемых значений для теста."""

    state: AsyncMock


@pytest.fixture(params=[
    {"expected": False, "user_id": 1},
    {"expected": True, "user_id": 223957535},
    ])
def test_data(request: pytest.FixtureRequest) -> dict[str, bool | int]:
    return request.param

@pytest.fixture(name="mock_callback")
def f_mock_callback() -> AsyncMock:
    """Мокируем CallbackQuery."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.message = AsyncMock(spec=Message)
    callback.message.reply = AsyncMock()  # Мокируем метод reply
    callback.answer = AsyncMock()  # Мокируем асинхронный метод answer
    return callback

@pytest.fixture(params=["feedback_type:suggestion", "feedback_type:review"])
def feedback_data(request: pytest.FixtureRequest, mock_callback: AsyncMock) -> FeedbackData:
    """Фикстура возвращает callback и ожидаемые занчения для теста.

    Args:
        request: параметры для теста. поступающие значения callback'а клавиатуры inline_feedback
        mock_callback: коллбек.
    """
    param = request.param
    mock_callback.data = param

    feedback_type = mock_callback.data.split(":")[1]  # Извлекаем 'suggestion' или 'review'
    feedback_type_rus = FEEDBACK_TYPES[feedback_type]
    data: FeedbackData = {"callback": mock_callback,
            "expected_msg": FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus),
            "expected_fb_type": feedback_type,
            "expected_answer_msg": ANSWER_MSG.format(feedback_type_rus=feedback_type_rus),
            "expected_feedback_type_rus": feedback_type_rus}
    return data

@pytest.fixture(params=["alex"])
def feedback_name_form_data(request: pytest.FixtureRequest,
                            mock_message: AsyncMock,
                            mock_state: AsyncMock) -> FeedbackNameForm:
    """Фикстура возвращает мок Message, мок состояния памяти с значение для state.get_data и ожидаемое сообщение.

    Args:
        request: параметры для теста.
        mock_message: мок Message.
        mock_state: мок состояния памяти.
    """
    name = request.param
    mock_message.text = name
    msg = NAME_FORM_MSG.format(name=name.capitalize(), feedback_type_rus="предложение")
    mock_state.get_data.return_value = {"feedback_type_rus": "Предложение"}

    return {"message": mock_message,
            "expected_text": msg,
            "state": mock_state}

@pytest.fixture(params=["Тестовое сообщение."])
def feedback_text_form_data(request: pytest.FixtureRequest,
                            mock_message: AsyncMock) -> FeedbackTextData:
    """Фикстура возвращает мок Message, мок состояния памяти с значение для state.get_data и ожидаемое сообщение.

    Args:
        request: параметры для теста.
        mock_message: мок Message.
        mock_state: мок состояния памяти.
    """
    text = request.param
    mock_message.text = text

    return {"message": mock_message, "expected_text": text}
