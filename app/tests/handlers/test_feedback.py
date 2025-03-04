from unittest.mock import AsyncMock

from aiogram.enums.parse_mode import ParseMode

from app.handlers.feedback import feedback_name_form, feedback_text_form, feedback_type_form
from app.keyboards import back_to_start_keyboard, back_to_start_or_send_review_keyboard
from app.logic.feedback import LogicFeedback
from app.states import FeedbackForm
from app.tests.handlers.conftest import FeedbackData, FeedbackNameForm, FeedbackTextData


async def test_feedback_type_form(feedback_data: FeedbackData,
                                  mock_state: AsyncMock,
                                  mock_logic_feedback: LogicFeedback) -> None:
    """Тестириуем хендлер feedback_type_form.

    Args:
        feedback_data: словарь с колбеком и ожидаемыми значениями.
        mock_state: состояние памяти.
        mock_logic_feedback: логика для работы с ОС.
    """
    callback = feedback_data["callback"]
    expected_msg = feedback_data["expected_msg"]
    expected_fb_type = feedback_data["expected_fb_type"]
    expected_answer_msg = feedback_data["expected_answer_msg"]
    expected_feedback_type_rus = feedback_data["expected_feedback_type_rus"]
    expected_msg_id = feedback_data["expected_msg_id"]

    await feedback_type_form(callback, mock_state, mock_logic_feedback)

    callback.answer.assert_awaited_once_with(expected_answer_msg)  # callback.answer был вызван с правильным текстом
    mock_state.update_data.assert_awaited_once_with(  # mock_state.update_data был вызван с правильными данными
        feedback_type=expected_fb_type,
        feedback_type_rus=expected_feedback_type_rus,
        msg_id=expected_msg_id)
    # mock_state.set_state был вызван с правильным состоянием
    mock_state.set_state.assert_awaited_once_with(FeedbackForm.waiting_for_name)
    callback.message.answer.assert_awaited_once_with(  # callback.message.reply был вызван с правильными аргументами
        expected_msg,
        reply_markup=back_to_start_keyboard,
        parse_mode=ParseMode.MARKDOWN_V2,
    )

async def test_feedback_name_form(feedback_name_form_data: FeedbackNameForm) -> None:
    """Тестириуем хендлер feedback_name_form.

    Args:
        feedback_name_form_data: словарь с Message, state со значениями get_data и ожидаемыми значениями.
    """
    message = feedback_name_form_data["message"]
    expected_msg = feedback_name_form_data["expected_text"]
    state = feedback_name_form_data["state"]

    await feedback_name_form(message, state)

    state.get_data.assert_awaited_once()
    state.update_data.assert_awaited_once_with(name=message.text.capitalize(), msg_id=message.message_id)
    state.set_state.assert_awaited_once_with(FeedbackForm.waiting_for_text)
    message.answer.assert_awaited_once_with(expected_msg,
                                           reply_markup=back_to_start_keyboard,
                                           parse_mode=ParseMode.MARKDOWN_V2,)

async def test_feedback_text_form(feedback_text_form_data: FeedbackTextData, mock_state: AsyncMock) -> None:
    """Тестириуем хендлер feedback_text_form.

    Args:
        feedback_text_form_data: словарь с Message и ожидаемыми значениями.
        mock_state: состояние памяти.
    """
    message = feedback_text_form_data["message"]
    expected_msg = feedback_text_form_data["expected_text"]

    await feedback_text_form(message, mock_state)

    mock_state.update_data.assert_awaited_once_with(text=expected_msg, msg_id=message.message_id)
    mock_state.set_state.assert_awaited_once_with(FeedbackForm.photo)
    message.answer.assert_awaited_once_with("Загрузите фотографию\\. \\(*Не обязательно*\\.\\)",
                                           reply_markup=back_to_start_or_send_review_keyboard,
                                           parse_mode=ParseMode.MARKDOWN_V2)
