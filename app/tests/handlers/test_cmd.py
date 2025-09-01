from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.handlers.user import cmd_start


@pytest.mark.asyncio()
async def test_cmd_start(
        test_data: dict[str, bool | int],
        user_logic_with_set_user_mock: AsyncMock,
        mock_fms_context_with_get_data: AsyncMock,
        mock_message_user_configure_for_cmd_start: AsyncMock,
        mock_wait_typing: MagicMock | AsyncMock,
        ) -> None:
    """Тест cmd_start для администратора.

    Кнопка 'Admin' должна отображаться в клавиатуре.

    Args:
        test_data: словарь, в котором ждем ожидаемое значение, с ключом expected
        user_logic_with_set_user_mock: Мок метод set_user объекта UserLogic
        mock_fms_context_with_get_data: Мокаем get_data объекта FSMContext
        mock_message_user_configure_for_cmd_start: Мок с параметрами объект User, который принадлежит Message
        mock_wait_typing: Мок wait_typing
    """
    expected = test_data["expected"]

    await cmd_start(
            mock_message_user_configure_for_cmd_start,
            mock_fms_context_with_get_data,
            user_logic_with_set_user_mock,
            )

    # 3. Проверки (Assertions):
    user_logic_with_set_user_mock.set_user.assert_awaited_once()  # проверяем вызов set_user
    mock_fms_context_with_get_data.get_data.assert_awaited_once()  # проверяем вызов get_data
    mock_wait_typing.assert_awaited_once()
    mock_message_user_configure_for_cmd_start.answer.assert_called_once()  # Проверяем, что answer был вызван
    _, kwargs = mock_message_user_configure_for_cmd_start.answer.call_args  # Получаем именованные аргументы, переданные в answer
    reply_markup = kwargs["reply_markup"]

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
