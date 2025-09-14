from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Chat, Message, User

from app.logic.feedback import LogicFeedback
from app.services.message_manager import MessageManager


@pytest.fixture(name="mock_chat")
def f_mock_chat() -> AsyncMock:
    """Мокаем объект aiogram.types.Chat."""
    return AsyncMock(spec=Chat)

@pytest.fixture(name="mock_message")
def f_mock_message(mock_chat: AsyncMock) -> AsyncMock:
    """Мокируем Message.

    Args:
        mock_chat: Мок объекта aiogram.types.Chat.
    """
    message = AsyncMock(spec=Message)
    message.chat = mock_chat
    message.from_user = AsyncMock(spec=User)
    message.reply = AsyncMock()  # Мокируем метод reply
    message.answer = AsyncMock()  # Мокируем метод answer
    return message

@pytest.fixture()
def mock_state() -> FSMContext:
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
    logic_feedback = LogicFeedback()
    logic_feedback.get_user_id = AsyncMock()
    logic_feedback.update_user = AsyncMock()
    logic_feedback.create_feedback = AsyncMock()
    return logic_feedback


@pytest.fixture()
def mock_message_manager():
    """Мокаем MessageManager."""
    mock = AsyncMock(spec=MessageManager)
    return mock

@pytest.fixture(name="mock_bot")
def f_mock_bot() -> AsyncMock:
    """Мокаем Bot."""
    return AsyncMock(spec=Bot)
