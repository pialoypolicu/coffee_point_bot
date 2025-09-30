from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.configs import ADMIN_IDS, current_chat_id
from app.helpers import wait_typing
from app.keyboards import (
    CALLBACK_BACK_TO_START,
    back_to_start_keyboard,
    back_to_start_or_send_review_keyboard,
    create_main_keyboard,
    inline_feedback,
)
from app.logic.user_logic import UserLogic
from app.models.feedback_model import FeedbackModel
from app.schemas.feedback import FeedbackFinalState
from app.services.message_manager import MessageManager
from app.states import FeedbackForm

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


class LogicFeedback(FeedbackModel):
    """Класс для работы логики обратной связи."""

    def __init__(self) -> None:
        """Контрусктор логики обратной связи."""
        super().__init__()
        self.user_logic = UserLogic()

    @property
    def chat_id(self) -> int | None:
        """Возвращает текущий chat_id из контекста."""
        return current_chat_id.get()

    async def process_start_feedback_form(self,
                                          callback: CallbackQuery,
                                          state: FSMContext,
                                          message_manager: MessageManager) -> None:
        """Логика оформления фидбека, кнопка оставить отзыв/предложение.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(callback)

        message_id = callback.message.message_id

        await state.set_state(FeedbackForm.waiting_for_feedback_type)

        await message_manager.safe_edit_message(self.chat_id,
                                                message_id,
                                                self.START_FEEDBACK_MSG,
                                                inline_feedback,
                                                parse_mode=ParseMode.MARKDOWN_V2)

    async def process_feedback_type_form(self,
                                         callback: CallbackQuery,
                                         state: FSMContext,
                                         message_manager: MessageManager) -> str:
        """обработка выбора типа ОС от клиента. или кнопка 'Предложение' или 'Отзыв'.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        if (callback_data := callback.data) == CALLBACK_BACK_TO_START:
            await self.user_logic.execute_back_to_start(callback, state, message_manager)
            return "В начало"
        await state.set_state(FeedbackForm.waiting_for_name)

        feedback_type = callback_data.split(":")[1]  # Извлекаем 'suggestion' или 'review'

        message_id = callback.message.message_id

        msg, answer_msg = self.parse_answer_msgs(feedback_type)

        await message_manager.safe_edit_message(self.chat_id,
                                                message_id,
                                                msg,
                                                back_to_start_keyboard,
                                                parse_mode=ParseMode.MARKDOWN_V2)
        # message_for_user = await callback.message.answer(msg,
        #                                                 reply_markup=back_to_start_keyboard,
        #                                                 parse_mode=ParseMode.MARKDOWN_V2)
        await state.update_data(feedback_type=feedback_type,
                                feedback_type_rus=self.FEEDBACK_TYPES[feedback_type],
                                bot_message_id=message_id)
        return answer_msg

    async def process_feedback_name_form(self,
                                   message: Message,
                                   state: FSMContext,
                                   message_manager: MessageManager) -> None:
        state_data = await state.get_data()
        name = message.text.capitalize()
        msg = self.NAME_FORM_MSG.format(name=name, feedback_type_rus=state_data["feedback_type_rus"].lower())

        await state.set_state(FeedbackForm.waiting_for_text)
        # Удаляем сообщение пользователя
        await message_manager.delete_messages(self.chat_id, [message.message_id])
        # message_for_user = await message.answer(msg, reply_markup=back_to_start_keyboard, parse_mode=ParseMode.MARKDOWN_V2)
        await message_manager.safe_edit_message(self.chat_id,
                                                state_data["bot_message_id"],
                                                msg,
                                                back_to_start_keyboard,
                                                parse_mode=ParseMode.MARKDOWN_V2)
        await state.update_data(name=name)

    async def process_feedback_text_form(self,
                                         message: Message,
                                         state: FSMContext,
                                         message_manager: MessageManager) -> None:
        await message_manager.delete_messages(self.chat_id, [message.message_id])
        await state.set_state(FeedbackForm.photo)
        state_data = await state.get_data()

        feedback_text = self.prepare_text(state_data.get("name"), message.text)

        await message_manager.safe_edit_message(self.chat_id,
                                                state_data["bot_message_id"],
                                                feedback_text,
                                                back_to_start_or_send_review_keyboard,
                                                parse_mode=ParseMode.MARKDOWN_V2)
        # message_for_user = await message.answer("Загрузите фотографию\\. \\(*Не обязательно*\\.\\)",
        #                                     reply_markup=back_to_start_or_send_review_keyboard,
        #                                     parse_mode=ParseMode.MARKDOWN_V2)
        # await state.update_data(text=message.text, msg_id=message_for_user.message_id)
        await state.update_data(text=message.text)

    async def process_feedback_completion(self,
                                          callback: CallbackQuery,
                                          state: FSMContext,
                                          message_manager: MessageManager) -> None:
        """Общая логика завершения формы обратной связи.

        Args:
            message: объект сообщения. так же может поступить сообщение коллбека, оно может относиться к боту.
                Поэтому присутствует аргумент tg_id. если летит коллбек. то будет передан tg_id клиента.
            state: Состояния памяти.
            tg_id: телеграм id клиента.
        """
        data = await state.get_data()

        state_data = FeedbackFinalState(**data)

        tg_user_id = callback.from_user.id

        user_id = await self.get_user_id_from_db(tg_user_id)

        await self.save_feedback_in_db(state_data, user_id)

        coffee_point_keyboard = await self.collect_coffee_point_kb(state_data.coffee_point_id)

        text = state_data.text
        name = state_data.name
        await self.update_user_in_db(user_id, name)

        feedback_type = self.FEEDBACK_TYPES[state_data.feedback_type]

        final_feedback_msg = FINAL_FEEDBACK_MSG.format(name=name, feedback_type=feedback_type, text=text)

        # Добавляем информацию о фото, если оно было загружено
        if state_data.photo:
            final_feedback_msg += "Фото: Загружено\n\n"
        else:
            final_feedback_msg += "Фото: Не загружено\n\n"

        final_feedback_msg += r"*Спасибо за обратную связь\!*"
        await message_manager.safe_edit_text(self.chat_id,
                                             callback.message.message_id,
                                             final_feedback_msg,
                                             reply_markup=coffee_point_keyboard,
                                             parse_mode=ParseMode.MARKDOWN_V2)
        await state.clear()
