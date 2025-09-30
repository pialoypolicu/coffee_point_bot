from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards import (
    CALLBACK_FEEDBACK,
    CALLBACK_SEND_REVIEW,
    back_to_start_keyboard,
    back_to_start_or_send_review_keyboard,
)
from app.logger import Logger
from app.logic.feedback import LogicFeedback
from app.services.message_manager import MessageManager
from app.states import FeedbackForm

feedback_router = Router()


# если клиент прикрепляет не фото, когда хендлер ожидает исключительно только фото.
PHOTO_WRONG_MSG = "Пожалуйста, *прикрепите через скрепочку фотографию* или нажмите *Отправить без фото*\\."


@feedback_router.callback_query(F.data == CALLBACK_FEEDBACK)
async def start_feedback_form(callback: CallbackQuery,
                              state: FSMContext,
                              logic_feedback: LogicFeedback,
                              message_manager: MessageManager) -> None:
    """Входная точка старта сбора формы обратной связи.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        logic_feedback: логикиа оформления обратной связи.
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await logic_feedback.process_start_feedback_form(callback, state, message_manager)

    await message_manager.safe_callback_answer(callback, "Вы выбрали 'Оставить отзыв/предложение'.")

@feedback_router.callback_query(FeedbackForm.waiting_for_feedback_type)
async def feedback_type_form(callback: CallbackQuery,
                             state: FSMContext,
                             logic_feedback: LogicFeedback,
                             message_manager: MessageManager) -> None:
    """получаем тип ОС, это предложение suggestion или review отзыв.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        logic_feedback: логикиа оформления обратной связи.
        message_manager:Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    answer_msg = await logic_feedback.process_feedback_type_form(callback, state, message_manager)

    await message_manager.safe_callback_answer(callback, answer_msg)

@feedback_router.message(FeedbackForm.waiting_for_name, F.text)
async def feedback_name_form(message: Message,
                             state: FSMContext,
                             logic_feedback: LogicFeedback,
                             message_manager: MessageManager) -> None:
    """получаем имя пользователя.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
        logic_feedback: middleware LogicFeedback
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await logic_feedback.process_feedback_name_form(message, state, message_manager)

@feedback_router.message(FeedbackForm.waiting_for_text, ~F.text)  # '~' ожидаем все что угодно, кроме текстового сообщ.
@feedback_router.message(FeedbackForm.waiting_for_name, ~F.text)
async def handle_non_text_message(message: Message, state: FSMContext, logger: Logger) -> None:
    """Обрабатывает некорректные сообщения (не текст) в состоянии waiting_for_name."""
    msg = "Пожалуйста, введите текстовое сообщение."
    logger.add_message += "\nХендлер ждет текстового сообщения, клиент отправил что то другое."
    logger.level = "warning"

    state_data = await state.get_data()
    if msg_id := state_data.get("msg_id"):
        await message.bot.send_message(text=msg,
                                       chat_id=message.chat.id,
                                       reply_to_message_id=msg_id,
                                       reply_markup=back_to_start_keyboard)
    else:
        await message.answer(msg, reply_markup=back_to_start_keyboard)

# TODO: нужно согласие для телефона.
# @feedback_router.message(FeedbackForm.waiting_for_phone)
# async def process_phone(message: Message, state: FSMContext):
#     """Получаем номер телефона пользователя"""
#     await state.update_data(phone=message.text)
#     await state.set_state(FeedbackForm.waiting_for_feedback_type)
#     await message.reply("Выберите тип обратной связи:", reply_markup=inline_feedback)

@feedback_router.message(FeedbackForm.waiting_for_text, F.text)
async def feedback_text_form(message: Message,
                             state: FSMContext,
                             logic_feedback: LogicFeedback,
                             message_manager: MessageManager) -> None:
    """получаем текст предложения/отзыва.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
        logic_feedback: middleware LogicFeedback
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await logic_feedback.process_feedback_text_form(message, state, message_manager)

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

@feedback_router.message(FeedbackForm.photo, ~F.photo)  # '~' ожидаем все что угодно, кроме фото.
async def handle_non_photo_message(message: Message, state: FSMContext, logger: Logger) -> None:
    """Обрабатывает некорректные сообщения (не текст) в состоянии waiting_for_name."""
    logger.log("не корректные данные, ждем фото.", level="warning")
    state_data = await state.get_data()
    if msg_id := state_data.get("msg_id"):
        await message.bot.send_message(text=PHOTO_WRONG_MSG,
                                    reply_markup=back_to_start_or_send_review_keyboard,
                                    chat_id=message.chat.id,
                                    reply_to_message_id=msg_id,
                                    parse_mode=ParseMode.MARKDOWN_V2)
    else:
        message.answer(PHOTO_WRONG_MSG,
                       reply_markup=back_to_start_or_send_review_keyboard,
                       parse_mode=ParseMode.MARKDOWN_V2)

@feedback_router.callback_query(F.data == CALLBACK_SEND_REVIEW)
async def feedback_photo_optional(callback: CallbackQuery,
                                  state: FSMContext,
                                  logic_feedback: LogicFeedback,
                                  message_manager: MessageManager) -> None:
    """Обработка завершения формы без фото.

    Args:
        callback: объект входящий запрос колбека
        state: Состояния памяти.
        logic_feedback: middleware LogicFeedback
    """
    await logic_feedback.process_feedback_completion(callback, state, message_manager)
    await message_manager.safe_callback_answer(callback)
