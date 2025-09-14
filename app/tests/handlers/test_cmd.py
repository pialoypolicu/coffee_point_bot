from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.handlers.user import cmd_start
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager


@pytest.mark.asyncio()
async def test_cmd_start(
        test_data: dict[str, bool | int],
        test_user_logic: UserLogic,
        mock_fms_context_with_get_data: AsyncMock,
        mock_message_user_configure_for_cmd_start: AsyncMock,
        mock_set_user: AsyncMock,
        mock_wait_typing: MagicMock | AsyncMock,
        test_message_manager: MessageManager,
        ) -> None:
    """Тест cmd_start для администратора.

    Кнопка 'Admin' должна отображаться в клавиатуре.

    Args:
        test_data: словарь, в котором ждем ожидаемое значение, с ключом expected
        test_user_logic:Объект UserLogic.
        mock_fms_context_with_get_data: Мокаем get_data объекта FSMContext
        mock_message_user_configure_for_cmd_start: Мок с параметрами объект User, который принадлежит Message
        mock_set_user: Мок UserContext.set_user.
        mock_wait_typing: Мок wait_typing
        test_message_manager: Объект MessageManager.
    """
    expected = test_data["expected"]

    await cmd_start(
            mock_message_user_configure_for_cmd_start,
            mock_fms_context_with_get_data,
            test_user_logic,
            test_message_manager,
            )

    # 3. Проверки (Assertions):
    mock_set_user.assert_awaited_once()  # проверяем вызов set_user
    mock_fms_context_with_get_data.get_data.assert_awaited_once()  # проверяем вызов get_data
    mock_wait_typing.assert_awaited_once()  # проверяем вызов метода wait_typing
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
