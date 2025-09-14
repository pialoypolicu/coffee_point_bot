from typing import TypedDict
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.database.requests.user import UserContext
from app.handlers.feedback import NAME_FORM_MSG
from app.logic.feedback import ANSWER_MSG, FEEDBACK_STEPS_MSG, FEEDBACK_TYPES
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager


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


@pytest.fixture()
def test_message_manager(mock_bot: AsyncMock) -> MessageManager:
    """Объект MessageManager.

    Args:
        mock_bot: Мок Bot.
    """
    return MessageManager(mock_bot)

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

@pytest.fixture()
def test_user_logic() -> UserLogic:
    """Объект UserLogic."""
    return UserLogic()

@pytest.fixture(name="mock_fms_context")
def f_mock_fms_context() -> AsyncMock:  # TODO: отказаться от этойфикстуры в пользу mock_state, в tests/conftest.py
    """Мокаем объект FSMContext, чтобы имитировать администратора."""
    return AsyncMock(spec=FSMContext)

@pytest.fixture()
def mock_fms_context_with_get_data(mock_fms_context: AsyncMock) -> AsyncMock:
    """Мокаем get_data объекта FSMContext.

    Args:
        mock_fms_context (AsyncMock): Мок объект FSMContext
    """
    mock_fms_context.get_data.return_value = {}
    return mock_fms_context

@pytest.fixture()
def mock_message_user_configure_for_cmd_start(mock_message: AsyncMock, test_data: dict[str, bool | int]):
    """Конфигурируем параметрами объект User, который принадлежит Message.

    Args:
        mock_message (AsyncMock): Мок Message
        test_data (dict[str, bool  |  int]): параметры для теста.
    """
    mock_message.from_user.configure_mock(
        id=test_data["user_id"],
        username="testuser",
        first_name="Test",
        last_name="User",
        full_name="Test User",
        )
    mock_message.chat.id = 17
    return mock_message

@pytest.fixture()
def mock_wait_typing():
    """Мокаем wait_typing."""
    with patch("app.logic.user_logic.wait_typing", new_callable=AsyncMock) as m:
        yield m

@pytest.fixture()
def mock_set_user():
    """Мокаем UserContext.set_user."""
    with patch.object(UserContext, "set_user", new_callable=AsyncMock) as mock:
        yield mock
