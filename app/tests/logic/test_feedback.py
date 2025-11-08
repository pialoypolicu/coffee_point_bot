from unittest.mock import AsyncMock

from aiogram.enums.parse_mode import ParseMode

from app.keyboards import back_to_start_keyboard
from app.logic.feedback import LogicFeedback
from app.states import FeedbackForm
from app.tests.logic.conftest import LogicFeedbackData, LogicFeedbackMainMsgs, LogicFeedbackStateName, LogicFeedbackTypeForm


# @pytest.mark.asyncio
async def test_process_feedback_completion(logic_feedback_data: LogicFeedbackData,
                                           mock_message_manager: AsyncMock,
                                           mock_get_user_id: AsyncMock,
                                           mock_update_user: AsyncMock,
                                           mock_create_feedback: AsyncMock) -> None:
    """тестируем фуункцию, отвечающую за финальное оформление отзыва.

    Args:
        logic_feedback_data: содержит данамические данные для теста.
        mock_message_manager: Мок MessageManager.
        mock_get_user_id: Фикстура мокает асинхронный метод get_user_id.
        mock_update_user: Фикстура мокает асинхронный метод update_user.
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
    mock_update_user.assert_awaited_once()

async def test_process_feedback_type_form(
        mock_logic_feedback_with_params: LogicFeedbackMainMsgs,
        mocks_handler_type_form: LogicFeedbackTypeForm,
        ) -> None:
    mock_callback = mocks_handler_type_form["mock_callback"]
    mock_state = mocks_handler_type_form["mock_state"]
    mock_message_manager = mocks_handler_type_form["mock_message_manager"]
    mock_logic_feedback = mock_logic_feedback_with_params["mock_logic_feedback"]

    exp_main_msg = mock_logic_feedback_with_params["expected_main_msg"]
    exp_answer_msg = mock_logic_feedback_with_params["expected_answer_msg"]
    exp_keyboard = mock_logic_feedback_with_params["expected_keyboard"]
    expected_feedback_type = mock_callback.data.split(":")[1]
    expected_feedback_type_rus = mock_logic_feedback.FEEDBACK_TYPES[expected_feedback_type]
    expected_message_id = mock_callback.message.message_id

    answer_msg = await mock_logic_feedback.process_feedback_type_form(mock_callback, mock_state, mock_message_manager)

    mock_state.set_state.assert_awaited_once_with(FeedbackForm.waiting_score)
    mock_message_manager.safe_edit_message.assert_awaited_once_with(mock_callback.message.chat.id,
                                                                    mock_callback.message.message_id,
                                                                    exp_main_msg,
                                                                    exp_keyboard,
                                                                    parse_mode=ParseMode.MARKDOWN_V2)
    mock_state.update_data.assert_awaited_once_with(feedback_type=expected_feedback_type,
                                                    feedback_type_rus=expected_feedback_type_rus,
                                                    bot_message_id=expected_message_id)
    assert answer_msg == exp_answer_msg

async def test_process_feedback_name_form(
        mock_state_with_params: LogicFeedbackStateName,
        mock_logic_feedback_with_name: LogicFeedbackMainMsgs,
        ) -> None:
    logic_feedback = mock_logic_feedback_with_name["mock_logic_feedback"]
    mock_message = mock_state_with_params["mock_message"]
    mock_state = mock_state_with_params["mock_state"]
    mock_message_manager = mock_state_with_params["mock_message_manager"]

    exp_chat_id = mock_message.chat.id
    exp_message_id = mock_message.message_id
    exp_name = mock_message.text.capitalize()
    exp_main_msg = mock_logic_feedback_with_name["expected_main_msg"]

    await logic_feedback.process_feedback_name_form(mock_message, mock_state, mock_message_manager)

    mock_state.get_data.assert_awaited_once()
    mock_state.set_state.assert_awaited_once_with(FeedbackForm.waiting_for_text)
    mock_message_manager.delete_messages.assert_awaited_once_with(exp_chat_id, [exp_message_id])
    mock_message_manager.safe_edit_message.assert_awaited_once_with(exp_chat_id,
                                                                    exp_message_id,
                                                                    exp_main_msg,
                                                                    back_to_start_keyboard,
                                                                    parse_mode=ParseMode.MARKDOWN_V2)
    mock_state.update_data.assert_awaited_once_with(name=exp_name)

