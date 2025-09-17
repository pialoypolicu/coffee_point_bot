from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.configs import ADMIN_IDS
from app.database.models import DrinkResult
from app.database.requests.keyboards import IngredientNamesHint
from app.database.requests.user import CoffeePointHint, UserContext, UserDataHint
from app.keyboards import (
    CALLBACK_BACK_TO_START,
    CALLBACK_COFFEE_POINT_PREFIX,
    CALLBACK_ITEM_PREFIX,
    create_main_keyboard_with_points,
    create_point_keyboard,
    inline_builder,
)


class UserModel(UserContext):
    """Модель для работы с сервисом Юзера."""

    async def set_user(self, message: Message) -> None:
        """Логика проверки и записи юзера в БД.

        Args:
            message: объект сообщения.
        """
        user_data: UserDataHint = {"tg_id": message.from_user.id,
                                   "tg_username": message.from_user.username,
                                    "first_name": message.from_user.first_name,
                                    "full_name": message.from_user.full_name,
                                    "last_name": message.from_user.last_name,
                                    "been_deleted": False}
        user = await self.get_user(user_id=message.from_user.id)
        if not user:
            await self.set_user_to_db(user_data=user_data)

    async def get_coffee_points(self) -> list[CoffeePointHint]:
        """Логика олучения кофейных точек."""
        return await self.get_coffee_points_db()

    async def get_main_keyboard(self,
                                message: Message | CallbackQuery,
                                coffee_points: list[CoffeePointHint]) -> InlineKeyboardMarkup:
        """логика создания главное клавиатуры. Учитывается является ли юзер админом.

        Args:
            message: объект сообщения.
            coffee_points (list[CoffeePointHint]): список кофейных точек
        """
        is_admin_user = message.from_user.id in ADMIN_IDS  # Проверяем, является ли пользователь админом
        return create_main_keyboard_with_points(is_admin_user, coffee_points)

    async def get_coffee_point_info_from_db(self, point_id: int) -> CoffeePointHint | None:
        """логика выборки карточки кофейной точки.

        Args:
            point_id: id кофейной точки.
        """
        return await self.get_coffee_point_info_db(point_id)

    @staticmethod
    async def collect_coffee_point_kb(point_id: int) -> InlineKeyboardMarkup:
        """Логика создания карточки кнопок кофейной точки.

        Args:
            point_id: id кофейной точки.
        """
        prev_step = {"text": "Вернуться в начало", "callback_data": CALLBACK_BACK_TO_START}
        return create_point_keyboard(point_id, prev_step=prev_step)

    @staticmethod
    def collect_names_with_inline_bld(names: list[IngredientNamesHint], point_id: int) -> InlineKeyboardMarkup:
        """Логика создания клавиаторы со списком напитков в кофейной точке.

        Args:
            names: список напитков
            point_id: id кофейной точки.
        """
        prev_callback = f"{CALLBACK_COFFEE_POINT_PREFIX}{point_id}"
        return inline_builder(names, prev_callback_data=prev_callback)

    async def get_names_from_db(self, coffee_point_id: int) -> list[IngredientNamesHint]:
        """Логика выборки напитков кофейни.

        Args:
            coffee_point_id: id кофейной точки.
        """
        return await self.get_names_db(coffee_point_id=coffee_point_id)

    async def get_drink_detail_from_db(self, callback_data: str) -> DrinkResult:
        """логика выборки карточки/свойств/оисание напитка.

        Args:
            callback_data: значение, отлавливаемое хендлером колбека.
        """
        item_id = int(callback_data.replace(CALLBACK_ITEM_PREFIX, ""))
        return await self.get_drink_detail_db(item_id=item_id)
