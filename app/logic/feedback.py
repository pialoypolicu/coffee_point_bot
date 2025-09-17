from datetime import datetime

from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.configs import ADMIN_IDS, current_chat_id
from app.database.requests.feedback import FeedbackContext
from app.helpers import wait_typing
from app.keyboards import (
    CALLBACK_BACK_TO_START,
    back_to_start_keyboard,
    create_main_keyboard,
    inline_feedback,
)
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager
from app.states import FeedbackForm

FEEDBACK_TYPES = {"suggestion": "Предложение", "review": "Отзыв"}

START_FEEDBACK_MSG = "Давайте заполним форму обратной связи\\.\n\n*Выберете тип обратной связи*:"
#  финальное сообщения после оформления ОС.
FINAL_FEEDBACK_MSG = (
            "*Форма обратной связи заполнена:*\n\n"
            "Имя: {name}\n"
            "Тип: {feedback_type}\n"
            "Текст: {text}\n"
        )
# сообщение информирующее какой выбран тип ОС + о предстоящих шагах.
FEEDBACK_STEPS_MSG = ("Вы выбрали *{feedback_type_rus}*\\.\n*Шаги для заполнения формы:*\n"
                    "\\- *Имя*\n"
                    "\\- *Текст*\n"
                    "\\- *Фото* \\(*не обязательно*\\)\n\n"
                        "*Пожалуйста, введите ваше имя*:")
# сообщение о выборе после нажатия кклавиши.
ANSWER_MSG = "Вы выбрали {feedback_type_rus}"

class LogicFeedback(FeedbackContext):
    """Класс для работы логики обратной связи."""

    def __init__(self) -> None:
        """Контрусктор логики обратной связи."""
        self.user_logic = UserLogic()

    @property
    def chat_id(self) -> int | None:
        """Возвращает текущий chat_id из контекста."""
        return current_chat_id.get()

    @staticmethod
    async def process_start_feedback_form(callback: CallbackQuery,
                                          state: FSMContext,
                                          message_manager: MessageManager) -> None:
        """Логика оформления фидбека, кнопка оставить отзыв/предложение.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(callback)

        chat_id = callback.message.chat.id
        message_id = callback.message.message_id

        await callback.answer("Вы выбрали 'Оставить отзыв/предложение'.")
        await state.clear()  # Сбрасываем состояние, если форма уже была запущена
        await state.set_state(FeedbackForm.waiting_for_feedback_type)

        await message_manager.safe_edit_message(
            chat_id, message_id,
            START_FEEDBACK_MSG,
            inline_feedback,
            parse_mode=ParseMode.MARKDOWN_V2,
            )

    async def process_feedback_type_form(
            self,
            callback: CallbackQuery,
            state: FSMContext,
            message_manager: MessageManager,
            ) -> None:
        """обработка выбора типа ОС от клиента. или кнопка 'Предложение' или 'Отзыв'.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        if (callback_data := callback.data) == CALLBACK_BACK_TO_START:
            await self.user_logic.execute_start_command(callback, state, message_manager)
            return
        feedback_type = callback_data.split(":")[1]  # Извлекаем 'suggestion' или 'review'
        feedback_type_rus = FEEDBACK_TYPES[feedback_type]
        msg = FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus)
        answer_msg = ANSWER_MSG.format(feedback_type_rus=feedback_type_rus)

        await callback.answer(answer_msg)
        await state.set_state(FeedbackForm.waiting_for_name)
        message_for_user = await callback.message.answer(msg,
                                                        reply_markup=back_to_start_keyboard,
                                                        parse_mode=ParseMode.MARKDOWN_V2)
        await state.update_data(feedback_type=feedback_type,
                                feedback_type_rus=feedback_type_rus,
                                msg_id=message_for_user.message_id)

    async def process_feedback_completion(self, message: Message, state: FSMContext, tg_id: int | None = None) -> None:
        """Общая логика завершения формы обратной связи.

        Args:
            message: объект сообщения. так же может поступить сообщение коллбека, оно может относиться к боту.
                Поэтому присутствует аргумент tg_id. если летит коллбек. то будет передан tg_id клиента.
            state: Состояния памяти.
            tg_id: телеграм id клиента.
        """
        tg_user_id = tg_id or message.from_user.id
        is_admin_user = tg_user_id in ADMIN_IDS  # Проверяем, является ли пользователь админом
        main_keyboard = create_main_keyboard(is_admin_user)

        state_data = await state.get_data()
        text = state_data["text"]
        name = state_data.pop("name")

        user_id = await self.get_user_id(tg_user_id=tg_user_id)
        state_data |= {"user_id": user_id}
        feedback_type = state_data["feedback_type"]
        user_data = {"name": name, "update_dt": datetime.now()}
        await self.update_user(user_id=user_id, data=user_data)

        await self.create_feedback(state_data)
        feedback_type = FEEDBACK_TYPES[feedback_type]

        final_feedback_msg = FINAL_FEEDBACK_MSG.format(name=name, feedback_type=feedback_type, text=text)

        # Добавляем информацию о фото, если оно было загружено
        if state_data.get("photo"):
            final_feedback_msg += "Фото: Загружено\n\n"
        else:
            final_feedback_msg += "Фото: Не загружено\n\n"

        final_feedback_msg += r"*Спасибо за обратную связь\!*"

        await message.reply(final_feedback_msg, reply_markup=main_keyboard, parse_mode=ParseMode.MARKDOWN_V2)
        await state.clear()
