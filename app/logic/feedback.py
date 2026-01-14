from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.configs import current_chat_id
from app.helpers import wait_typing
from app.keyboards import (
    CALLBACK_BACK_TO_START,
    back_to_start_keyboard,
    back_to_start_or_send_review_keyboard,
    inline_feedback,
)
from app.logic.user_logic import UserLogic
from app.models.feedback_model import FeedbackModel
from app.schemas.feedback import FeedbackFinalState, FeedBackType
from app.services.media_service import MediaServiceManager
from app.services.message_manager import MessageManager
from app.states import FeedbackForm


class LogicFeedback(FeedbackModel):
    """Класс для работы логики обратной связи."""

    def __init__(self) -> None:
        """Контрусктор логики обратной связи."""
        super().__init__()
        self.user_logic = UserLogic()
        self.media_group_manager = MediaServiceManager(max_photos=10, process_delay=1.0)

    @property
    def chat_id(self) -> int | None:
        """Возвращает текущий chat_id из контекста."""
        return current_chat_id.get()

    async def process_start_feedback_form(
        self, callback: CallbackQuery, state: FSMContext, message_manager: MessageManager
    ) -> None:
        """Логика оформления фидбека, кнопка оставить отзыв/предложение.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(callback)

        message_id = callback.message.message_id

        await state.set_state(FeedbackForm.waiting_for_feedback_type)

        await message_manager.safe_edit_message(
            self.chat_id, message_id, self.START_FEEDBACK_MSG, inline_feedback, parse_mode=ParseMode.MARKDOWN_V2
        )

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

        feedback_type: FeedBackType = callback_data.split(":")[1]  # Извлекаем 'suggestion' или 'review'

        await self.feedback_set_step(state, feedback_type)

        message_id = callback.message.message_id

        main_msg, answer_msg = self.parse_answer_msgs(feedback_type)
        keyboard = self.parse_keyboard(feedback_type)

        await message_manager.safe_edit_message(
            self.chat_id, message_id, main_msg, keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        await state.update_data(
            feedback_type=feedback_type,
            feedback_type_rus=self.FEEDBACK_TYPES[feedback_type],
            bot_message_id=message_id,
        )
        return answer_msg

    async def process_feedback_score_form(self,
                                          callback: CallbackQuery,
                                          state: FSMContext,
                                          message_manager: MessageManager) -> str:
        """обработка выбора типа ОС от клиента. или кнопка 'Предложение' или 'Отзыв'.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        callback_data_score = callback.data
        message_id = callback.message.message_id
        score_value = self.parse_score(callback_data_score)
        clean_markdown = False

        answer_for_client, ans = await self.parse_score_text(state, score_value)
        if score_value < self.max_score:
            await state.update_data(feedback_type="review_score", score_value=score_value)
            await self.feedback_set_step(state, feedback_type="suggestion")
            clean_markdown = True

        await message_manager.safe_edit_message(self.chat_id,
                                                message_id,
                                                answer_for_client,
                                                back_to_start_keyboard,
                                                clean_markdown=clean_markdown,
                                                parse_mode=ParseMode.MARKDOWN_V2)
        return ans

    # WARN: Возможно это более не понадобится.
    # async def process_client_message_to_admin(self,message: Message, message_manager: MessageManager):
    #     text = message.text
    #     admin_message = await self.collect_client_message_for_admin(text)
    #     your_chat_id = ADMIN_IDS[0]  # Берем первый ID из списка администраторов
    #     await message_manager.safe_send_message(chat_id=your_chat_id, text=admin_message)
    #     await message_manager.delete_messages(self.chat_id, [message.message_id])
    #     await message_manager.safe_send_message(
    #         self.chat_id, "Сообщение отправлено.", reply_markup=back_to_start_keyboard
    #     )

    async def process_feedback_name_form(self,
                                         message: Message,
                                         state: FSMContext,
                                         message_manager: MessageManager) -> None:
        """Логика обработки имени клиента, при оформлении ОС.

        Args:
            message: объект сообщения.
            state: Состояния памяти.
            message_manager:  Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        state_data = await state.get_data()
        name = message.text.capitalize()
        score_value = state_data.get("score_value")
        tip_hint = "Теперь введите ваше сообщение"
        msg, _ = self.parse_answer_msgs(state_data["feedback_type"], name, score_value=score_value, tip_hint=tip_hint)
        await state.set_state(FeedbackForm.waiting_for_text)
        # Удаляем сообщение пользователя
        await message_manager.delete_messages(self.chat_id, [message.message_id])
        await message_manager.safe_edit_message(
            self.chat_id, state_data["bot_message_id"], msg, back_to_start_keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )
        await state.update_data(name=name)

    async def process_feedback_text_form(self,
                                         message: Message,
                                         state: FSMContext,
                                         message_manager: MessageManager) -> None:
        """Логика обработки введенного текста клиента с его ОС.

        Args:
            message: объект сообщения.
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await message_manager.delete_messages(self.chat_id, [message.message_id])
        await state.set_state(FeedbackForm.photo)
        state_data = await state.get_data()
        tip_hint = "Подтвердите, нажав кнопку <Отправить>"
        # feedback_text = self.prepare_text(state_data.get("name"), message.text)
        feedback_text, answer_msg = self.parse_answer_msgs(
            state_data["feedback_type"], name=state_data["name"], text=message.text, tip_hint=tip_hint
        )

        await message_manager.safe_edit_message(
            self.chat_id, state_data["bot_message_id"], feedback_text, back_to_start_or_send_review_keyboard
        )
        await state.update_data(text=message.text)
        return answer_msg

    async def process_feedback_completion(self,
                                          callback: CallbackQuery | Message,
                                          state: FSMContext,
                                          message_manager: MessageManager) -> None:
        """Общая логика завершения формы обратной связи.

        Args:
            callback: объект сообщения. так же может поступить сообщение коллбека, оно может относиться к боту.
                Поэтому присутствует аргумент tg_id. если летит коллбек. то будет передан tg_id клиента.
            state: Состояния памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        message_id = callback.message.message_id if isinstance(callback, CallbackQuery) else callback.message_id
        data = await state.get_data()
        state_data = FeedbackFinalState(**data)
        tg_user_id = callback.from_user.id
        text = state_data.text
        name = state_data.name
        feedback_type = self.FEEDBACK_TYPES[state_data.feedback_type]
        final_feedback_msg = self.FINAL_FEEDBACK_MSG.format(name=name, feedback_type=feedback_type, text=text)

        user_id = await self.get_user_id_from_db(tg_user_id)
        await self.save_feedback_in_db(state_data, user_id)
        coffee_point_keyboard = await self.collect_coffee_point_kb(state_data.coffee_point_id)
        await self.update_user_in_db(user_id, name)
        await message_manager.safe_edit_text(self.chat_id,
                                             message_id,
                                             final_feedback_msg,
                                             reply_markup=coffee_point_keyboard,
                                             parse_mode=ParseMode.MARKDOWN_V2)
        await state.clear()

    # WARN: Для обработки группы фоток, пока не ясно, нужно будет ли это в будущем.
    # async def process_feedback_completion_with_group_photo(self, message: Message, state: FSMContext) -> None:
    #     if message.video:
    #         return None
    #     await self.media_group_manager.add_to_media_group(message, state)
