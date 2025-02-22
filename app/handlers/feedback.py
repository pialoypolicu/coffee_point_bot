from datetime import datetime

from aiogram import F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.requests.feedback import create_feedback
from app.database.requests.user import get_user_id, update_user
from app.keyboards import inline_feedback
from app.states import FeedbackForm

feedback_router = Router()

FEEDBACK_TYPES = {"suggestion": "Предложение", "review": "Отзыв"}

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
    feedback_type = callback.data.split(':')[1]  # Извлекаем 'suggestion' или 'review'
    msg = f"Вы выбрали *{FEEDBACK_TYPES[feedback_type]}*\\.\n\n*Введите ваше имя*:"
    await state.update_data(feedback_type=feedback_type)
    await state.set_state(FeedbackForm.waiting_for_name)
    await callback.message.reply(msg, parse_mode=ParseMode.MARKDOWN_V2)

@feedback_router.message(FeedbackForm.waiting_for_name)
async def feedback_name_form(message: Message, state: FSMContext) -> None:
    """получаем имя пользователя.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
    """
    name = message.text
    await state.update_data(name=name)
    await state.set_state(FeedbackForm.waiting_for_text)
    await message.reply(f"{name.capitalize()}, оставьте отзыв/предложение:")

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
    await message.reply("Загрузите фотографию.")


@feedback_router.message(FeedbackForm.photo, F.photo)
async def feedback_photo_form(message: Message, state: FSMContext) -> None:
    """Получаем фото от пользователя.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
    """
    await state.update_data(photo=message.photo[-1].file_id)
    state_data = await state.get_data()
    tg_user_id = message.from_user.id
    name = state_data.pop("name")

    user_id = await get_user_id(tg_user_id=tg_user_id)
    state_data |= {"user_id": user_id}
    feedback_type = state_data["feedback_type"]
    user_data = {"name": name, "update_dt": datetime.now()}
    await update_user(user_id=user_id, data=user_data)

    await create_feedback(state_data)

    feedback_message = (
        "*Форма обратной связи заполнена:*\n\n"
        f"Имя: {name}\n"
        f"Тип: {FEEDBACK_TYPES[feedback_type]}\n"
        f"Текст: {state_data['text']}\n\n"
        r"*Спасибо за обратную связь\!*"
        )
    await message.reply(feedback_message, parse_mode=ParseMode.MARKDOWN_V2)
    await state.clear()
