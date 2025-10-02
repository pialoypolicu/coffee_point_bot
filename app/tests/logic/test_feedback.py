from unittest.mock import AsyncMock

from aiogram.enums.parse_mode import ParseMode

from app.tests.logic.conftest import LogicFeedbackData


# @pytest.mark.asyncio
async def test_process_feedback_completion(logic_feedback_data: LogicFeedbackData,
                                           mock_message_manager: AsyncMock,
                                           mock_get_user_id: AsyncMock,
                                           mock_create_feedback: AsyncMock) -> None:
    """тестируем фуункцию, отвечающую за финальное оформление отзыва.

    Args:
        logic_feedback_data: содержит данамические данные для теста.
        mock_message_manager: Мок MessageManager.
        mock_get_user_id: Фикстура мокает асинхронный метод get_user_id.
        mock_create_feedback: Фикстура мокает асинхронный метод create_feedback.
    """
    # Вызываем тестируемый метод
    state = logic_feedback_data["state"]
    mock_callback = logic_feedback_data["mock_callback"]
    logic_feedback = logic_feedback_data["logic_feedback"]
    expected_final_message = logic_feedback_data["expected_final_msg"]
    expected_tg_user_id = mock_callback.from_user.id
    expected_coffee_point_keyboard = logic_feedback_data["expected_coffee_point_keyboard"]

    await logic_feedback.process_feedback_completion(mock_callback, state, mock_message_manager)

    mock_get_user_id.assert_awaited_once_with(tg_user_id=expected_tg_user_id)
    mock_create_feedback.assert_awaited_once()
    state.clear.assert_awaited_once()

    # Проверяем, что сообщение отправлено с правильным текстом
    mock_message_manager.safe_edit_text.assert_awaited_once_with(
        mock_callback.message.chat.id,
        mock_callback.message.message_id,
        expected_final_message,
        reply_markup=expected_coffee_point_keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )
