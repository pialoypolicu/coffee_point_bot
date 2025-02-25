from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.fsm.context import FSMContext

import pytest
from aiogram.types import InlineKeyboardMarkup, Message, User

from app.handlers.user import cmd_start


@pytest.mark.asyncio()
async def test_cmd_start(test_data: dict[str, bool | int]):
    """
    Тест cmd_start для администратора.
    Кнопка 'Admin' должна отображаться в клавиатуре.
    """
    expected, user_id = test_data["expected"], test_data["user_id"]
    # 1. Мокируем объекты Message, FSMContext и User, чтобы имитировать администратора
    # TODO: вынести в моки в фикстуру.
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock(spec=User,
                                       id=user_id,
                                       username="testuser",
                                       first_name="Test",
                                       last_name="User",
                                       full_name="Test User")
    # message_mock.from_user = MagicMock(spec=User, id=user_id)  # Используем первый ID админа из ADMIN_IDS
    message_mock.answer = AsyncMock()  # Мокируем метод answer
    state_mock = AsyncMock(spec=FSMContext)
    state_mock.get_data.return_value = {}

    # 2. Патчим побочные эффекты (wait_typing и set_user), чтобы избежать их реального выполнения
    with patch("app.handlers.user.wait_typing", new_callable=AsyncMock), patch("app.handlers.user.set_user", new_callable=AsyncMock):
        await cmd_start(message_mock, state_mock)

    # 3. Проверки (Assertions):
    message_mock.answer.assert_called_once()  # Проверяем, что answer был вызван один раз
    _, kwargs = message_mock.answer.call_args  # Получаем именованные аргументы, переданные в answer
    reply_markup = kwargs['reply_markup']

    assert isinstance(reply_markup, InlineKeyboardMarkup), "Reply markup должен быть InlineKeyboardMarkup"

    admin_button_found = False
    for row in reply_markup.inline_keyboard:
        for button in row:
            if button.text == "Admin":
                admin_button_found = True
                break
        if admin_button_found:
            break

    assert admin_button_found is expected, "Кнопка Admin должна присутствовать для администратора"
