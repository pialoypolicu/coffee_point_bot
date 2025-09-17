from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.handlers.user import (
    back_to_start,
    coffee_point_handler,
    command_start_points,
    drink_item_handler,
    get_coffee_point_drinks,
)
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager
from app.tests.handlers.conftest import CallbackItemHint, CallbackPointHint


@pytest.mark.asyncio()
async def test_comand_start_points(
        test_data: dict[str, bool | int],
        test_user_logic: UserLogic,
        mock_fms_context_with_get_data: AsyncMock,
        mock_message_user_configure_for_cmd_start: AsyncMock,
        mock_set_user_to_db: AsyncMock,
        mock_wait_typing: MagicMock | AsyncMock,
        test_message_manager: MessageManager,
        mock_get_coffee_points_db: AsyncMock,
        mock_safe_send_message: AsyncMock,
        mock_get_user: AsyncMock,
        ) -> None:
    """Тест хедлера command_start_points для администратора и нет.

    Если 'Admin' кнока должна отображаться.

    Args:
        test_data: словарь, в котором ждем ожидаемое значение, с ключом expected
        test_user_logic: Объект UserLogic.
        mock_fms_context_with_get_data: Мок get_data объекта FSMContext
        mock_message_user_configure_for_cmd_start: Мок с параметрами объект User, который принадлежит Message
        mock_set_user_to_db: Мок UserContext.set_user.
        mock_wait_typing: Мок wait_typing
        test_message_manager: Объект MessageManager.
        mock_get_coffee_points_db: Мок функции UserContext.get_coffee_points_db.
        mock_safe_send_message: Мок функции MessageManager.safe_send_message.
        mock_get_user: Мок функции UserContext.get_user.
    """
    expected = test_data["expected"]

    await command_start_points(
            mock_message_user_configure_for_cmd_start,
            mock_fms_context_with_get_data,
            test_user_logic,
            test_message_manager,
            )

    # 3. Проверки (Assertions):
    mock_set_user_to_db.assert_awaited_once()  # проверяем вызов set_user
    mock_get_user.assert_awaited_once()
    mock_fms_context_with_get_data.get_data.assert_awaited_once()  # проверяем вызов get_data
    mock_fms_context_with_get_data.get_state.assert_awaited_once()
    mock_fms_context_with_get_data.clear.assert_awaited_once()
    mock_wait_typing.assert_awaited_once()  # проверяем вызов метода wait_typing
    mock_get_coffee_points_db.assert_awaited_once()
    mock_safe_send_message.assert_awaited_once()
    _, kwargs = mock_safe_send_message.call_args  # Получаем именованные аргументы, переданные в safe_send_message
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

@pytest.mark.asyncio()
async def test_coffee_point_handler(
        mock_calback_with_params: CallbackPointHint,
        test_user_logic: UserLogic,
        mock_wait_typing: AsyncMock,
        mock_message_manager: AsyncMock,
        mock_get_coffee_point_info_from_db: AsyncMock,
        ) -> None:
    """тестируем хендлер coffee_point_handler.

    Args:
        mock_calback_with_params: параметризированный мок CallbackQuery.
        test_user_logic: Объект UserLogic.
        mock_wait_typing: Мок wait_typing
        mock_message_manager: Мок MessageManager.
        mock_get_coffee_point_info_from_db: Мок функцию UserContext.get_coffee_point_info_db.
    """
    mock_callback_query = mock_calback_with_params["mock"]
    expected_point_id = mock_calback_with_params["expected_point_id"]

    await coffee_point_handler(mock_callback_query, test_user_logic, mock_message_manager)

    mock_get_coffee_point_info_from_db.assert_awaited_once_with(expected_point_id)
    mock_wait_typing.assert_awaited_once()
    mock_message_manager.safe_callback_answer.assert_awaited_once()
    mock_message_manager.safe_edit_message.assert_awaited_once()

@pytest.mark.asyncio()
async def test_get_coffee_point_drinks(
        mock_calback_with_params_drinks_point: CallbackPointHint,
        mock_state_with_params: AsyncMock,
        test_user_logic: UserLogic,
        mock_wait_typing: AsyncMock,
        mock_message_manager: AsyncMock,
        mock_get_names_db: AsyncMock,
) -> None:
    """тестируем хендлер get_coffee_point_drinks.

    Args:
        mock_calback_with_params_drinks_point: мок CallbackQuery с конфигурацией.
        mock_state_with_params: мок FSMContext с конфигурацией.
        test_user_logic: Объект UserLogic.
        mock_wait_typing: Мок wait_typing
        mock_message_manager: Мок MessageManager.
        mock_get_names_db: Мок функцию UserContext.get_names_db.
    """
    mock_callback_query = mock_calback_with_params_drinks_point["mock"]
    expected_point_id = mock_calback_with_params_drinks_point["expected_point_id"]

    await get_coffee_point_drinks(mock_callback_query, mock_state_with_params, test_user_logic, mock_message_manager)

    mock_message_manager.safe_edit_message.assert_awaited_once()
    mock_get_names_db.assert_awaited_once()
    mock_state_with_params.update_data.assert_awaited_once_with(point_id=expected_point_id)
    mock_wait_typing.assert_awaited_once()

@pytest.mark.asyncio()
async def test_drink_item_handler(
        mock_calback_with_params_drink_item: CallbackItemHint,
        mock_state_with_params_coffee_item: AsyncMock,
        test_user_logic: UserLogic,
        mock_wait_typing: AsyncMock,
        mock_message_manager: AsyncMock,
        mock_get_drink_detail_db: AsyncMock,
) -> None:
    """тестируем хендлер drink_item_handler.

    Args:
        mock_calback_with_params_drink_item: мок CallbackQuery с конфигурацией.
        mock_state_with_params_coffee_item: мок FSMContext с конфигурацией.
        test_user_logic: Объект UserLogic.
        mock_wait_typing: Мок wait_typing
        mock_message_manager: Мок MessageManager.
        mock_get_drink_detail_db: Мок функцкию UserContext.get_drink_detail_db.
    """
    mock_callback_query = mock_calback_with_params_drink_item["mock"]
    expected_item_id = mock_calback_with_params_drink_item["expected_item_id"]

    await drink_item_handler(mock_callback_query, mock_state_with_params_coffee_item, test_user_logic, mock_message_manager)

    mock_state_with_params_coffee_item.get_data.assert_awaited_once()
    mock_get_drink_detail_db.assert_awaited_once_with(item_id=expected_item_id)
    mock_wait_typing.assert_awaited_once()
    mock_message_manager.safe_edit_message.assert_awaited_once()

@pytest.mark.asyncio()
async def test_back_to_start(
        mock_calback_with_params_back_to_start: AsyncMock,
        mock_state_with_params_coffee_item: AsyncMock,
        test_user_logic: UserLogic,
        mock_message_manager: AsyncMock,
        mock_get_coffee_points_db: AsyncMock,
) -> None:
    """Тестируем хендлер back_to_start.

    Args:
        mock_calback_with_params_back_to_start: мок CallbackQuery с конфигурацией..
        mock_state_with_params_coffee_item: мок FSMContext с конфигурацией.
        test_user_logic: Объект UserLogic.
        mock_message_manager: Мок MessageManager.
        mock_get_coffee_points_db: Мок функцию UserContext.get_coffee_points_db.
    """
    await back_to_start(mock_calback_with_params_back_to_start, mock_state_with_params_coffee_item, test_user_logic, mock_message_manager)

    mock_message_manager.safe_callback_answer.assert_awaited_once()
    mock_state_with_params_coffee_item.get_data.assert_awaited_once()
    mock_state_with_params_coffee_item.clear.assert_awaited_once()
    mock_message_manager.safe_edit_message.assert_awaited_once()
    mock_get_coffee_points_db.assert_awaited_once()
