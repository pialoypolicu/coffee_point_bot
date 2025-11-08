from collections.abc import Generator
from typing import TypedDict
from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from app.keyboards import CALLBACK_BACK_TO_START, create_point_keyboard
from app.logic.feedback import FINAL_FEEDBACK_MSG, LogicFeedback
from app.models.feedback_model import FeedbackModel


class LogicFeedbackData(TypedDict):
    """Хинт коллекции фикстуры logic_feedback_data."""

    state: AsyncMock
    mock_callback: AsyncMock
    expected_final_msg: str
    expected_coffee_point_keyboard: InlineKeyboardMarkup
    logic_feedback: LogicFeedback

class LogicFeedbackTypeForm(TypedDict):
    """Хинт коллекции фиктуры mocks_handler_type_form."""

    mock_callback: AsyncMock
    mock_state: AsyncMock
    mock_message_manager: AsyncMock


class LogicFeedbackMainMsgs(TypedDict):
    mock_logic_feedback: LogicFeedback
    expected_main_msg: str
    expected_answer_msg: str
    expected_keyboard: InlineKeyboardMarkup


class LogicFeedbackStateName(TypedDict):

    mock_state: AsyncMock
    mock_message: AsyncMock
    mock_message_manager: AsyncMock


@pytest.fixture(params=["photo_file_id", None])
def logic_feedback_data(request: pytest.FixtureRequest,
                        mock_state: AsyncMock,
                        fixt_feedback_model: FeedbackModel,
                        mock_logic_feedback: LogicFeedback,
                        mock_callback: AsyncMock) -> Generator[LogicFeedbackData, None, None]:
    """Фикстура подготавливает динамические данные.

    Отрабатывает два кейса. когда клиент отправляет фото и ккогда не отправляет.

    Args:
        request: параметризация теста.
        mock_state: состояние памяти.
        fixt_feedback_model: Фикстура с логикой модели для работы с ОС от клиента.
        mock_logic_feedback: логика работы с отзывами.
        mock_callback: сообщение клиента.
    """
    kb = create_point_keyboard(1, {"text": "Вернуться в начало", "callback_data": CALLBACK_BACK_TO_START})
    photo = request.param
    name = "Иван"
    feedback_type = "suggestion"
    text = "test Отличный бот!"
    feedback_type_rus = fixt_feedback_model.FEEDBACK_TYPES[feedback_type]
    final_feedback_msg = FINAL_FEEDBACK_MSG.format(name=name, feedback_type=feedback_type_rus, text=text)
    if photo:
        final_feedback_msg += "Фото: Загружено\n\n"
    else:
        final_feedback_msg += "Фото: Не загружено\n\n"
    final_feedback_msg += r"*Спасибо за обратную связь\!*"

    mock_state.get_data.return_value = {"coffee_point_id": 1,
                                        "bot_message_id": 123,
                                        "feedback_type": feedback_type,
                                        "feedback_type_rus": feedback_type_rus,
                                        "name": name,
                                        "text": text,
                                        "photos": photo}
    yield {"state": mock_state,
            "mock_callback": mock_callback,
            "expected_final_msg": final_feedback_msg,
            "expected_coffee_point_keyboard": kb,
            "logic_feedback": mock_logic_feedback}
    mock_state.reset_mock()

@pytest.fixture()
def mocks_handler_type_form(
        mock_callback: AsyncMock,
        mock_state_clean: AsyncMock,
        mock_message_manager: AsyncMock
        ) -> LogicFeedbackTypeForm:
    mock_callback.data = "feedback_type:review"

    return {"mock_callback": mock_callback,
            "mock_state": mock_state_clean,
            "mock_message_manager": mock_message_manager}

@pytest.fixture()
def mock_logic_feedback_with_params(mock_logic_feedback: LogicFeedback) -> LogicFeedbackMainMsgs:
    expected_main_msg, answer_msg = mock_logic_feedback.parse_answer_msgs("review")
    keyboard = mock_logic_feedback.parse_keyboard("review")

    return {"mock_logic_feedback": mock_logic_feedback,
            "expected_main_msg": expected_main_msg,
            "expected_answer_msg": answer_msg,
            "expected_keyboard": keyboard}

@pytest.fixture()
def mock_state_with_params(
        mock_state_clean: AsyncMock,
        mock_message: AsyncMock,
        mock_message_manager: AsyncMock
        ) -> LogicFeedbackStateName:
    mock_state_clean.get_data.return_value = {"feedback_type": "review",
                                              "feedback_type_rus": "Отзыв",
                                              "bot_message_id": mock_message.message_id}
    mock_message.text = "alex"
    return {"mock_state": mock_state_clean, "mock_message": mock_message, "mock_message_manager": mock_message_manager}

@pytest.fixture()
def mock_logic_feedback_with_name(
        mock_logic_feedback: LogicFeedback,
        mock_state_with_params: LogicFeedbackStateName,
        ) -> LogicFeedbackMainMsgs:
    mock_message = mock_state_with_params["mock_message"]
    name = mock_message.text.capitalize()
    tip_hint = "Теперь введите ваше сообщение"
    expected_main_msg, answer_msg = mock_logic_feedback.parse_answer_msgs("review", name=name, tip_hint=tip_hint)

    return {"mock_logic_feedback": mock_logic_feedback,
            "expected_main_msg": expected_main_msg,
            "expected_answer_msg": answer_msg}
