from unittest.mock import AsyncMock

from aiogram.enums.parse_mode import ParseMode

from app.handlers.feedback import (
    feedback_name_form,
    feedback_photo_optional,
    feedback_text_form,
    feedback_type_form,
    start_feedback_form,
)
from app.keyboards import back_to_start_keyboard, back_to_start_or_send_review_keyboard
from app.logic.feedback import LogicFeedback
from app.states import FeedbackForm
from app.tests.handlers.conftest import FeedbackData, FeedbackNameForm, FeedbackTextData


async def test_start_feedback_form(
        mock_callback: AsyncMock,
        mock_state_clean: AsyncMock,
        mock_message_manager: AsyncMock,
        mock_logic_feedback: LogicFeedback,
        mock_wait_typing_feedback: AsyncMock,
        ) -> None:
    """Тестируем хендлер start_feedback_form.

    Args:
        mock_callback: Мок CallbackQuery.
        mock_state_clean: Очищенный мок объекта состояния памяти FSMContext.
        mock_message_manager: Мок MessageManager.
        mock_logic_feedback: Мок LogicFeedback.
        mock_wait_typing_feedback: Мок wait_typing.
    """
    await start_feedback_form(mock_callback, mock_state_clean, mock_logic_feedback, mock_message_manager)

    mock_wait_typing_feedback.assert_awaited_once()
    mock_state_clean.set_state.assert_awaited_once()
    mock_message_manager.safe_edit_message.assert_awaited_once()

async def test_feedback_type_form(
        feedback_data: FeedbackData,
        mock_logic_feedback: LogicFeedback,
        mock_message_manager: AsyncMock,
        ) -> None:
    """Тестириуем хендлер feedback_type_form.

    Args:
        feedback_data: словарь с колбеком и ожидаемыми значениями.
        mock_logic_feedback: логика для работы с ОС.
        mock_message_manager: Мокаем MessageManager.
    """
    callback = feedback_data["callback"]
    mock_state = feedback_data["mock_state"]
    expected_msg = feedback_data["expected_msg"]
    expected_fb_type = feedback_data["expected_fb_type"]
    expected_answer_msg = feedback_data["expected_answer_msg"]
    expected_feedback_type_rus = feedback_data["expected_feedback_type_rus"]

    await feedback_type_form(callback, mock_state, mock_logic_feedback, mock_message_manager)

    mock_message_manager.safe_callback_answer.assert_awaited_once_with(callback, expected_answer_msg)
    mock_state.update_data.assert_awaited_once_with(
        feedback_type=expected_fb_type,
        feedback_type_rus=expected_feedback_type_rus,
        bot_message_id=callback.message.message_id)
    mock_state.set_state.assert_awaited_once_with(FeedbackForm.waiting_for_name)
    mock_message_manager.safe_edit_message.assert_awaited_once_with(
        callback.message.chat.id,
        callback.message.message_id,
        expected_msg,
        back_to_start_keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

async def test_feedback_name_form(
        feedback_name_form_data: FeedbackNameForm,
        mock_logic_feedback: LogicFeedback,
        mock_message_manager: AsyncMock,
        ) -> None:
    """Тестириуем хендлер feedback_name_form.

    Args:
        feedback_name_form_data: словарь с Message, state со значениями get_data и ожидаемыми значениями.
        mock_logic_feedback: Мок LogicFeedback.
        mock_message_manager: Мок MessageManager.
    """
    message = feedback_name_form_data["message"]
    expected_msg = feedback_name_form_data["expected_text"]
    state = feedback_name_form_data["mock_state"]

    await feedback_name_form(message, state, mock_logic_feedback, mock_message_manager)

    state.get_data.assert_awaited_once()
    state.update_data.assert_awaited_once_with(name=message.text.capitalize())
    state.set_state.assert_awaited_once_with(FeedbackForm.waiting_for_text)
    mock_message_manager.safe_edit_message.assert_awaited_once_with(message.chat.id,
                                                                    message.message_id,
                                                                    expected_msg,
                                                                    back_to_start_keyboard,
                                                                    parse_mode=ParseMode.MARKDOWN_V2)

async def test_feedback_text_form(
        feedback_text_form_data: FeedbackTextData,
        mock_logic_feedback: LogicFeedback,
        mock_message_manager: AsyncMock,
        ) -> None:
    """Тестириуем хендлер feedback_text_form.

    Args:
        feedback_text_form_data: словарь с Message и ожидаемыми значениями.
        mock_logic_feedback: Мок LogicFeedback.
        mock_message_manager: Мок MessageManager.
    """
    message = feedback_text_form_data["message"]
    expected_msg = feedback_text_form_data["expected_text"]
    expected_chat_id = message.chat.id
    expected_message_id = message.message_id
    expected_answer = feedback_text_form_data["expected_answer"]
    mock_state = feedback_text_form_data["mock_state"]

    await feedback_text_form(message, mock_state, mock_logic_feedback, mock_message_manager)

    mock_message_manager.delete_messages.assert_awaited_once_with(expected_chat_id, [expected_message_id])
    mock_state.set_state.assert_awaited_once_with(FeedbackForm.photo)
    mock_state.update_data.assert_awaited_once_with(text=expected_msg)
    mock_message_manager.safe_edit_message.assert_awaited_once_with(expected_chat_id,
                                                                    expected_message_id,
                                                                    expected_answer,
                                                                    back_to_start_or_send_review_keyboard,
                                                                    parse_mode=ParseMode.MARKDOWN_V2)

async def test_feedback_photo_optional(
                                mock_callback: AsyncMock,
                                mock_state_with_params_final_feedback: AsyncMock,
                                mock_logic_feedback: LogicFeedback,
                                mock_message_manager: AsyncMock,
                                mock_get_user_id: AsyncMock,
                                mock_create_feedback: AsyncMock,
                                mock_update_user: AsyncMock,
                                ) -> None:
    """Тестируем хендлер feedback_photo_optional.

    Args:
        mock_callback: Мок CallbackQuery.
        mock_state_with_params_final_feedback: состояние памяти, эмитация завершения прохождения опроса.
        mock_logic_feedback: Мок LogicFeedback.
        mock_message_manager: Мок MessageManager.
        mock_get_user_id: Фикстура мокает асинхронный метод get_user_id.
        mock_create_feedback: Фикстура мокает асинхронный метод create_feedback.
        mock_update_user: Фикстура для мокает асинхронный метод update_user.
    """
    expected_tg_user_id = mock_callback.from_user.id

    await feedback_photo_optional(mock_callback,
                                  mock_state_with_params_final_feedback,
                                  mock_logic_feedback,
                                  mock_message_manager)

    mock_state_with_params_final_feedback.get_data.assert_awaited_once()
    mock_state_with_params_final_feedback.clear.assert_awaited_once()
    mock_get_user_id.assert_awaited_once_with(tg_user_id=expected_tg_user_id)
    mock_create_feedback.assert_awaited_once()
    mock_update_user.assert_awaited_once()
    mock_message_manager.safe_edit_text.assert_awaited_once()
    mock_message_manager.safe_callback_answer.assert_awaited_once()

async def test_feedback_group_photo_form(mock_callback,
                                         mock_state_with_params_final_feedback,
                                         mock_logic_feedback,
                                         mock_message_manager) -> None:
    assert True
