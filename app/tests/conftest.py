from collections.abc import Generator
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Chat, Message, User
from pytest_mock import MockerFixture

from app.database.requests.feedback import FeedbackContext
from app.logic.feedback import LogicFeedback
from app.models.feedback_model import FeedbackModel
from app.services.message_manager import MessageManager

AsyncMockGenerator = Generator[AsyncMock, None, None]


@pytest.fixture(name="mock_chat")
def f_mock_chat() -> AsyncMock:
    """Мокаем объект aiogram.types.Chat."""
    mock = AsyncMock(spec=Chat)
    mock.id = 167
    return mock

@pytest.fixture(name="mock_user")
def f_mock_user() -> AsyncMock:
    """Мокаем объект aiogram.types.User."""
    mock = AsyncMock(spec=User)
    mock.id = 777
    return mock

@pytest.fixture(name="fixt_feedback_model")
def f_feedback_model() -> FeedbackModel:
    """Фикстура с логикой модели для работы с ОС от клиента."""
    return FeedbackModel()

@pytest.fixture(name="mock_message")
def f_mock_message(mock_chat: AsyncMock, mock_user: AsyncMock) -> AsyncMock:
    """Мокируем Message.

    Args:
        mock_chat: Мок объекта aiogram.types.Chat.
        mock_user: Мок объекта aiogram.types.User.
    """
    message = AsyncMock(spec=Message)
    message.message_id = 77
    message.chat = mock_chat
    message.from_user = mock_user
    message.reply = AsyncMock()  # Мокируем метод reply
    message.answer = AsyncMock()  # Мокируем метод answer
    return message

@pytest.fixture(name="mock_callback")
def f_mock_callback(mock_message: AsyncMock, mock_user: AsyncMock) -> AsyncMock:
    """Мокируем CallbackQuery.

    Args:
        mock_message: Мок Message.
        mock_user: Мок объекта aiogram.types.User.
    """
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = mock_user
    callback.message = mock_message
    callback.message.answer = AsyncMock(return_value=mock_message)  # Мокируем метод answer
    callback.answer = AsyncMock()  # Мокируем асинхронный метод answer
    return callback

@pytest.fixture(scope="session", name="mock_state")
def f_mock_state() -> AsyncMock:
    """Мокируем FSMContext."""
    state = AsyncMock(spec=FSMContext)
    state.update_data = AsyncMock()  # Мокируем метод update_data
    state.set_state = AsyncMock()  # Мокируем метод set_state
    state.get_data = AsyncMock()  # Мокируем метод get_data
    state.clear = AsyncMock()
    return state

@pytest.fixture(name="mock_logic_feedback")
def f_mock_feedback() -> LogicFeedback:
    """Мокируем методы LogicFeedback."""
    return LogicFeedback()

@pytest.fixture()
def mock_message_manager() -> AsyncMock:
    """Мокаем MessageManager."""
    mock = AsyncMock(spec=MessageManager)
    return mock

@pytest.fixture(name="mock_bot")
def f_mock_bot() -> AsyncMock:
    """Мокаем Bot."""
    return AsyncMock(spec=Bot)

@pytest.fixture(autouse=True)
def mock_chat_id(mock_chat: AsyncMock) -> AsyncMockGenerator:
    """Мокаем проперти self.chat_id.

    Args:
        mock_chat: Мок объекта aiogram.types.Chat.
    """
    with patch.object(LogicFeedback, "chat_id", new_callable=PropertyMock) as mock:
        mock.return_value = mock_chat.id  # Устанавливаем нужное значение
        yield mock

@pytest.fixture()
def mock_get_user_id(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для мокирования асинхронного метода get_user_id."""
    return mocker.patch.object(FeedbackContext, "get_user_id", new_callable=AsyncMock, return_value=1)

@pytest.fixture()
def mock_create_feedback(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для мокирования асинхронного метода create_feedback."""
    return mocker.patch.object(FeedbackContext, "create_feedback", new_callable=AsyncMock)

@pytest.fixture()
def mock_update_user(mocker: MockerFixture) -> AsyncMock:
    """Фикстура для мокирования асинхронного метода update_user."""
    return mocker.patch.object(FeedbackContext, "update_user", new_callable=AsyncMock)
