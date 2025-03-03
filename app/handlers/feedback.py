from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards import back_to_start_keyboard, back_to_start_or_send_review_keyboard, inline_feedback
from app.logic.feedback import FEEDBACK_TYPES, LogicFeedback
from app.middlewares.feedback import LogicFeedbackMiddleware
from app.states import FeedbackForm

feedback_router = Router()
feedback_router.message.middleware(LogicFeedbackMiddleware(LogicFeedback()))
feedback_router.callback_query.middleware(LogicFeedbackMiddleware(LogicFeedback()))


# сообщение информирующее какой выбран тип ОС + о предстоящих шагах.
FEEDBACK_STEPS_MSG = ("Вы выбрали *{feedback_type_rus}*\\.\n*Шаги для заполнения формы:*\n"
                    "\\- *Имя*\n"
                    "\\- *Текст*\n"
                    "\\- *Фото* \\(*не обязательно*\\)\n\n"
                        "*Введите ваше имя*:")
# сообщение о выборе после нажатия кклавиши.
ANSWER_MSG = "Вы выбрали {feedback_type_rus}"
# сообщение  нструкция для отправки сообщения ОС,
NAME_FORM_MSG = "{name}, что бы оставить *{feedback_type_rus}*, введите сообщение:"


@feedback_router.callback_query(F.data == "feedback")
async def start_feedback_form(callback: CallbackQuery, state: FSMContext) -> None:
    """Входная точка старта сбора формы обратной связи.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    msg = "Давайте заполним форму обратной связи\\.\n\n*Выберете тип обратной связи*:"
    await callback.answer("Вы выбрали Оставить отзыв/предложение.")
    await state.clear()  # Сбрасываем состояние, если форма уже была запущена
    await state.set_state(FeedbackForm.waiting_for_feedback_type)
    await callback.message.reply(msg, reply_markup=inline_feedback, parse_mode=ParseMode.MARKDOWN_V2)

@feedback_router.callback_query(FeedbackForm.waiting_for_feedback_type)
async def feedback_type_form(callback: CallbackQuery, state: FSMContext) -> None:
    """получаем тип ОС, это предложение suggestion или review отзыв.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    feedback_type = callback.data.split(":")[1]  # Извлекаем 'suggestion' или 'review'
    feedback_type_rus = FEEDBACK_TYPES[feedback_type]
    msg = FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus)
    answer_msg = ANSWER_MSG.format(feedback_type_rus=feedback_type_rus)

    await callback.answer(answer_msg)
    await state.update_data(feedback_type=feedback_type, feedback_type_rus=feedback_type_rus)
    await state.set_state(FeedbackForm.waiting_for_name)
    await callback.message.reply(msg, reply_markup=back_to_start_keyboard, parse_mode=ParseMode.MARKDOWN_V2)

@feedback_router.message(FeedbackForm.waiting_for_name)
async def feedback_name_form(message: Message, state: FSMContext) -> None:
    """получаем имя пользователя.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
    """
    state_data = await state.get_data()
    name = message.text.capitalize()
    msg = NAME_FORM_MSG.format(name=name, feedback_type_rus=state_data["feedback_type_rus"].lower())

    await state.update_data(name=name)
    await state.set_state(FeedbackForm.waiting_for_text)
    await message.reply(msg, reply_markup=back_to_start_keyboard, parse_mode=ParseMode.MARKDOWN_V2)

# TODO: нужно согласие для телефона.
# @feedback_router.message(FeedbackForm.waiting_for_phone)
# async def process_phone(message: Message, state: FSMContext):
#     """Получаем номер телефона пользователя"""
#     await state.update_data(phone=message.text)
#     await state.set_state(FeedbackForm.waiting_for_feedback_type)
#     await message.reply("Выберите тип обратной связи:", reply_markup=inline_feedback)

@feedback_router.message(FeedbackForm.waiting_for_text)
async def feedback_text_form(message: Message, state: FSMContext) -> None:
    """получаем текст предложения/отзыва.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
    """
    await state.update_data(text=message.text)
    await state.set_state(FeedbackForm.photo)
    await message.reply("Загрузите фотографию\\. \\(*Не обязательно*\\.\\)",
                        reply_markup=back_to_start_or_send_review_keyboard,
                        parse_mode=ParseMode.MARKDOWN_V2)

@feedback_router.message(FeedbackForm.photo, F.photo)
async def feedback_photo_form(message: Message, state: FSMContext, logic_feedback: LogicFeedback) -> None:
    """Получаем фото от пользователя.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
        logic_feedback: middleware LogicFeedback
    """
    await state.update_data(photo=message.photo[-1].file_id)
    await logic_feedback.process_feedback_completion(message, state)

@feedback_router.callback_query(F.data == "send_review")
async def feedback_photo_optional(callback: CallbackQuery, state: FSMContext, logic_feedback: LogicFeedback) -> None:
    """Обработка завершения формы без фото.

    Args:
        callback: объект входящий запрос колбека
        state: Состояния памяти.
        logic_feedback: middleware LogicFeedback
    """
    tg_id = callback.from_user.id
    await logic_feedback.process_feedback_completion(callback.message, state, tg_id)
