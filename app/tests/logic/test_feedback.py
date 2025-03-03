import pytest
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup

from app.tests.logic.conftest import LogicFeedbackData


@pytest.mark.asyncio
async def test_process_feedback_completion(logic_feedback_data: LogicFeedbackData,
                                           main_keyboard: InlineKeyboardMarkup) -> None:
    """тестируем фуункцию, отвечающую за финальное оформление отзыва.

    Args:
        logic_feedback_data: содержит данамические данные для теста.
        main_keyboard: индайн клавиатура с главной менюшкой.
    """
    # Вызываем тестируемый метод
    state = logic_feedback_data["state"]
    message = logic_feedback_data["message"]
    logic_feedback = logic_feedback_data["logic_feedback"]
    expected_final_message = logic_feedback_data["expected_final_msg"]
    await logic_feedback.process_feedback_completion(message, state)

    logic_feedback.get_user_id.assert_awaited_once_with(tg_user_id=123)
    # TODO: прилетает разная дата. нужно как то уровнять с вызываемой ддатой в коде и в тесте.ч1ч
    # logic_feedback.update_user.assert_awaited_once_with(user_id=1, data={"name": "Иван", "update_dt": datetime.now()})
    logic_feedback.create_feedback.assert_awaited_once()
    state.clear.assert_awaited_once()

    # Проверяем, что сообщение отправлено с правильным текстом
    message.reply.assert_awaited_once_with(expected_final_message, reply_markup=main_keyboard, parse_mode="MarkdownV2")
