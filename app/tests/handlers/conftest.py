from typing import TypedDict
from unittest.mock import AsyncMock

import pytest
from aiogram.types import CallbackQuery

from app.handlers.feedback import NAME_FORM_MSG
from app.logic.feedback import ANSWER_MSG, FEEDBACK_STEPS_MSG, FEEDBACK_TYPES


class FeedbackData(TypedDict):
    """Хинт колбека и ожидаемых значений для теста."""

    callback: AsyncMock
    expected_msg: str
    expected_fb_type: str
    expected_answer_msg: str
    expected_feedback_type_rus: str
    expected_msg_id: int

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
def f_mock_callback(mock_message: AsyncMock) -> AsyncMock:
    """Мокируем CallbackQuery."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.message = mock_message
    callback.message.answer = AsyncMock(return_value=mock_message)  # Мокируем метод answer
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
    mock_callback.message.message_id = 835

    feedback_type = mock_callback.data.split(":")[1]  # Извлекаем 'suggestion' или 'review'
    feedback_type_rus = FEEDBACK_TYPES[feedback_type]
    data: FeedbackData = {"callback": mock_callback,
            "expected_msg": FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus),
            "expected_fb_type": feedback_type,
            "expected_msg_id": 835,
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
    msg_id = 12
    mock_message.message_id = msg_id
    mock_message.answer.return_value = mock_message
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
    msg_id = 17
    mock_message.message_id = msg_id
    mock_message.answer.return_value = mock_message

    return {"message": mock_message, "expected_text": text}
