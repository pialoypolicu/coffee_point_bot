from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, User

from app.logic.feedback import LogicFeedback


@pytest.fixture(name="mock_message")
def f_mock_message() -> AsyncMock:
    """Мокируем Message."""
    message = AsyncMock(spec=Message)
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
