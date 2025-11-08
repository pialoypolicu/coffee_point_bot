from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup

from app.database.requests.feedback import FeedbackContext
from app.keyboards import CALLBACK_BACK_TO_START, back_to_start_keyboard, create_point_keyboard, inline_builder
from app.schemas.feedback import FeedbackCreateSchema, FeedbackFinalState, FeedBackType
from app.states import FeedbackForm


class FeedbackModel(FeedbackContext):
    """Класс модели для работы с ОС от клиента."""

    def __init__(self) -> None:
        """Инициализирует модель обратной связи с текстовыми шаблонами и конфигурацией процесса."""
        self.FEEDBACK_TYPES = {"suggestion": "Предложение", "review": "Отзыв", "review_score": "Оценка"}
        # self.START_FEEDBACK_MSG = "Давайте заполним форму обратной связи\\.\n\n*Выберете тип обратной связи*:"
        self.START_FEEDBACK_MSG = "Давайте заполним форму обратной связи.\n\n*Выберете тип обратной связи*:"
        # сообщение о выборе после нажатия кклавиши.
        self.ANSWER_MSG = "Вы выбрали {feedback_type_rus}"
        self.SCORE_MSG_STEP = "Ваша оценка: *{score_value}*"
        self.SUGGEST_MSG_STEP = "Вы выбрали *{feedback_type_rus}*."
        self.STEPS_MSG = ("\n*Шаги для заполнения формы:*\n"
                                                  "- *Имя*: {name}\n"
                                                  "- *Текст*: {text}\n"
                                                  "*{tip_hint}*:")
        # сообщение информирующее какой выбран тип ОС + о предстоящих шагах.
        self.FEEDBACK_STEPS_MSG = {"suggestion": f"{self.SUGGEST_MSG_STEP}{self.STEPS_MSG}",
                                   "review_score": f"{self.SCORE_MSG_STEP}{self.STEPS_MSG}",
                                    "review": "Оцените нас от 1 до 5"}
        # сообщение  нструкция для отправки сообщения ОС,
        self.NAME_FORM_MSG = "{name}, что бы оставить *{feedback_type_rus}*, пожалуйста, введите сообщение:"
        self.feedback_text = ("*Ваше обращение:*\n"
                              "*Имя*: {name}\n"
                              "*Введенный текст*: {text}\n"
                              "*Загрузите фотографию*\\. \\(*Не обязательно*\\.\\)")
        self.STATES = {"review": FeedbackForm.waiting_score,
                       "text_for_admin": FeedbackForm.waiting_text_for_admin,
                       "suggestion": FeedbackForm.waiting_for_name}
        self.max_score = 5
        self.text_to_admin = "Введите текст:"
        #  финальное сообщения после оформления ОС.
        self.FINAL_FEEDBACK_MSG = ("*Форма обратной связи заполнена:*\n\n"
                                   "Имя: {name}\n"
                                   "Тип: {feedback_type}\n"
                                   "Текст: {text}\n"
                                   "*Спасибо за обратную связь!*")

    async def feedback_set_step(self, state: FSMContext, feedback_type: FeedBackType) -> None:
        """Устанавливает шаг статуса ожидания сообщения от клиента.

        Args:
            state: Состояния памяти.
            feedback_type: Тип обратной связи.
        """
        await state.set_state(self.STATES[feedback_type])

    def parse_answer_msgs(self,
                          feedback_type: FeedBackType,
                          name: str = "",
                          text: str = "",
                          score_value: int | None = None,
                          tip_hint: str = "Пожалуйста, введите ваше имя") -> tuple[str, str]:
        """Подготавливает ответы для пользователя.

        Args:
            feedback_type: выбраный пользователем тип ОС.
            name: Введенное имя клиента.
            text: Введенный текст отзыва/ОС клиента.
            score_value: поставленая оценка в отзыве.
            tip_hint: подсказка для клиента.
        """
        feedback_type_rus = self.FEEDBACK_TYPES[feedback_type]
        message_patterns = self.FEEDBACK_STEPS_MSG[feedback_type]
        main_msg = message_patterns.format(feedback_type_rus=feedback_type_rus,
                                           name=name,
                                           text=text,
                                           score_value=score_value,
                                           tip_hint=tip_hint)
        answer_msg = self.ANSWER_MSG.format(feedback_type_rus=feedback_type_rus)
        return main_msg, answer_msg

    def prepare_text(self, name: str, text: str) -> str:
        """Подготавлливает текст для клиента.

        Args:
            name: имя клиента.
            text: текст клиента.
        """
        return self.feedback_text.format(name=name, text=text)

    async def get_user_id_from_db(self, tg_user_id: int) -> int:
        """Получить ID клиента.

        Args:
            tg_user_id (int): телеграмм ID клиента.
        """
        return await self.get_user_id(tg_user_id=tg_user_id)

    async def save_feedback_in_db(self, state_data: FeedbackFinalState, user_id: int) -> None:
        """Записать ОС клиента в БД.

        Args:
            state_data: состояние памяти.
            user_id: ID клиента.
        """
        data = FeedbackCreateSchema(**state_data.model_dump(), user_id=user_id)
        await self.create_feedback(data)

    async def update_user_in_db(self, user_id: int, name: str) -> None:
        """Обновить данныее клиента.

        Args:
            user_id: ID клиента.
            name: имя клиента.
        """
        data = {"name": name, "update_dt": datetime.now()}
        await self.update_user(user_id, data)

    @staticmethod
    async def collect_coffee_point_kb(point_id: int) -> InlineKeyboardMarkup:
        """Логика создания карточки кнопок кофейной точки.

        Args:
            point_id: id кофейной точки.
        """
        prev_step = {"text": "Вернуться в начало", "callback_data": CALLBACK_BACK_TO_START}
        return create_point_keyboard(point_id, prev_step=prev_step)

    def parse_keyboard(self, feedback_type: FeedBackType) -> InlineKeyboardMarkup:
        """Подготавливает keyboard в зависимости какой тип ОС выбрал клиент, предложение или отзыв.

        Args:
            feedback_type: Тип обратной связи.
        """
        if feedback_type == "review":
            # TODO: исправить типизацию в inline_builder, сейчас ожидается IngredientNamesHint
            names = [{"id": score, "name": f"{score}"} for score in range(1, self.max_score + 1)]
            return inline_builder(names,
                                  item="score_item_",
                                  prev_callback_data=CALLBACK_BACK_TO_START,
                                  prev_text="Вернуться в начало",
                                  adjust_number=self.max_score)
        return back_to_start_keyboard

    @staticmethod
    def parse_score(callback_data: str) -> int:
        """Распасить оценку и привести ее к инту.

        Args:
            callback_data: значение поступающие от клиента.
        """
        return int(callback_data.split("_")[-1])

    async def parse_score_text(self, state: FSMContext, score: int) -> tuple[str, str]:
        """Определяем какую оценку поставил клиент. Если максимально положительную, то отправляем его на ЯК.

        Если клиент оставил ниже максимальной, то подготавливаем форму для прохождения опроса.

        Args:
            state: Состояния памяти.
            score: Оценка клиента.
        """
        state_date = await state.get_data()
        if score == self.max_score:
            url = await self.get_feedback_link(state_date["coffee_point_id"])
            # TODO: завернуть ссылку в слово. а то получается партянка из символов.
            return f"Оставить отзыв, вы можете в *Яндекс Картах* перейдя по [ссылке]({url})", "Ваша оценка 5"
        return self.parse_answer_msgs("review_score", score_value=score)

    @staticmethod
    async def collect_client_message_for_admin(client_message: str,
                                              client_name: str = "Неизвестно",
                                              feedback_type: str = "Не указан",
                                              ) -> None:
        """Отправляет сообщение клиента администратору в личные сообщения.

        Args:
            client_message: Текст сообщения от клиента
            client_name: Имя клиента (если известно)
            feedback_type: Тип обратной связи
        """
        # Форматируем сообщение для администратора
        admin_message = (
            "📨 *Новое сообщение от клиента:*\n\n"
            f"*Имя:* {client_name}\n"
            f"*Тип обращения:* {feedback_type}\n"
            f"*Сообщение:* {client_message}\n"
            f"*Время:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return admin_message
