from datetime import datetime

from aiogram.types import InlineKeyboardMarkup

from app.database.requests.feedback import FeedbackContext
from app.keyboards import CALLBACK_BACK_TO_START, create_point_keyboard
from app.schemas.feedback import FeedbackCreateSchema, FeedbackFinalState


class FeedbackModel(FeedbackContext):
    """Класс модели для работы с ОС от клиента."""

    def __init__(self) -> None:
        """Инициализирует модель обратной связи с текстовыми шаблонами и конфигурацией процесса."""
        self.FEEDBACK_TYPES = {"suggestion": "Предложение", "review": "Отзыв"}
        self.START_FEEDBACK_MSG = "Давайте заполним форму обратной связи\\.\n\n*Выберете тип обратной связи*:"
        # сообщение о выборе после нажатия кклавиши.
        self.ANSWER_MSG = "Вы выбрали {feedback_type_rus}"
        # сообщение информирующее какой выбран тип ОС + о предстоящих шагах.
        self.FEEDBACK_STEPS_MSG = ("Вы выбрали *{feedback_type_rus}*\\.\n*Шаги для заполнения формы:*\n"
                                   "\\- *Имя*\n"
                                   "\\- *Текст*\n"
                                   "\\- *Фото* \\(*не обязательно*\\)\n\n"
                                   "*Пожалуйста, введите ваше имя*:")
        # сообщение  нструкция для отправки сообщения ОС,
        self.NAME_FORM_MSG = "{name}, что бы оставить *{feedback_type_rus}*, пожалуйста, введите сообщение:"
        self.feedback_text = ("*Ваше обращение:*\n"
                              "*Имя*: {name}\n"
                              "*Введенный текст*: {text}\n"
                              "*Загрузите фотографию*\\. \\(*Не обязательно*\\.\\)")

    def parse_answer_msgs(self, feedback_type: str) -> tuple[str, str]:
        """Подготавливает ответы для пользователя.

        Args:
            feedback_type: выбраный пользователем тип ОС.
        """
        feedback_type_rus = self.FEEDBACK_TYPES[feedback_type]

        msg = self.FEEDBACK_STEPS_MSG.format(feedback_type_rus=feedback_type_rus)
        answer_msg = self.ANSWER_MSG.format(feedback_type_rus=feedback_type_rus)

        return msg, answer_msg

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
