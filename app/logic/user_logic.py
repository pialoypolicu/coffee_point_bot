from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.configs import current_chat_id
from app.helpers import wait_typing
from app.keyboards import (
    CALLBACK_COFFEE_POINT_PREFIX,
    CALLBACK_DRINKS,
    back_to_start_keyboard,
    make_back_to_drinks_kb,
)
from app.models.user_model import UserModel
from app.services.media_service import MediaServiceManager
from app.services.message_manager import MessageManager


class UserLogic(UserModel):
    """класс логики для взаимодействия клиента с ботом."""

    def __init__(self) -> None:
        """Конструктор объекта взаимодействия клиента с ботом."""
        self.media_service = MediaServiceManager()

    @property
    def chat_id(self) -> int | None:
        """Возвращает текущий chat_id из контекста."""
        return current_chat_id.get()

    async def execute_comand_start_show_points(self,
                                               message: Message,
                                               state: FSMContext,
                                               message_manager: MessageManager) -> None:
        """Логика команды '/start'.

        Args:
            message: объект сообщения.
            state: состояние памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(message)
        await message_manager.delete_messages(self.chat_id, [message.message_id])
        msg = "Добро пожаловать в Coffee Point!"
        await self.set_user(message)

        if await state.get_data() or await state.get_state():
            await state.clear()

        await message_manager.cleanup_chat_messages(self.chat_id)

        # Получаем список кофейных точек
        coffee_points = await self.get_coffee_points()

        main_keyboard = await self.get_main_keyboard(message, coffee_points)

        await message_manager.safe_send_message(self.chat_id, msg, reply_markup=main_keyboard)

    async def get_all_drinks(self,
                             callback: CallbackQuery,
                             state: FSMContext,
                             message_manager: MessageManager) -> None:
        """Функция возвращает все напитки кофейни.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояние памяти
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(callback)

        message_id = callback.message.message_id
        point_id = int(callback.data.replace(CALLBACK_DRINKS, ""))

        await state.update_data(point_id=point_id)

        # if message_ids_to_delete := state_data.get("drink_msgs"):  # назад к списку напитков.
        #     await delete_messages(callback, [message_ids_to_delete["photo_msg_id"]])
        #     await state.clear()

        names = await self.get_names_from_db(coffee_point_id=point_id)
        drink_names_keyboard = self.collect_names_with_inline_bld(names, point_id)

        await message_manager.safe_edit_message(self.chat_id, message_id, "Выберете напиток", drink_names_keyboard)

    async def get_drink_detail(self, callback: CallbackQuery, state: FSMContext, message_manager: MessageManager) -> None:
        await wait_typing(callback)

        state_data = await state.get_data()
        # if message_ids_to_delete := state_data.get("drink_msgs"):  # возвращаемся к списку напитков.
        #     await delete_messages(callback, list(message_ids_to_delete.values()))
        #     await state.clear()
        message_id = callback.message.message_id
        point_id = state_data["point_id"]

        drink_detail = await self.get_drink_detail_from_db(callback.data)
        # await state.update_data(ingredients=result["ingredients"])

        # Удаляем сообщение со списком напитков
        # await callback.message.delete()

        # photo_message = await self.media_service.safe_send_photo(
        #     callback,
        #     photo_string=result["photos"][0]["photo_string"],
        #     caption=f"Напиток: {result["name"]}",
        #     show_caption_above_media=True,
        # )
        drink_text = f"Напиток: **{drink_detail['name']}**\n\nОписание напитка: {drink_detail['description']}"
        back_to_drinks = await make_back_to_drinks_kb(point_id)

        await message_manager.safe_edit_message(self.chat_id,
                                                message_id,
                                                drink_text,
                                                back_to_drinks,
                                                parse_mode=ParseMode.MARKDOWN)
        # await state.update_data(drink_msgs={"photo_msg_id": photo_message.message_id,
        #                                     "desc_msg_id": description_message.message_id},
        #                                     ingredients=result["ingredients"])

    # async def execute_start_command(self, message: Message, state: FSMContext, message_manager: MessageManager):
    #     """Логика командыы '/start'.

    #     Args:
    #         message: объект сообщения.
    #         state: состояние памяти.
    #         message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    #     """
    #     # Проверяем, не обрабатывали ли мы уже этот запрос
    #     await wait_typing(message)
    #     await message_manager.cleanup_chat_messages(message.chat.id)

    #     if await state.get_data():
    #         await state.clear()

    #     user_data: UserDataHint = {"tg_id": message.from_user.id,
    #                                "tg_username": message.from_user.username,
    #                                 "first_name": message.from_user.first_name,
    #                                 "full_name": message.from_user.full_name,
    #                                 "last_name": message.from_user.last_name,
    #                                 "been_deleted": False}
    #     await self.set_user(user_data)

    #     is_admin_user = message.from_user.id in ADMIN_IDS  # Проверяем, является ли пользователь админом
    #     main_keyboard = kb.create_main_keyboard(is_admin_user)  # Создаем клавиатуру динамически

    #     sent_message = await message.answer("Добро пожаловать в Coffee Point!", reply_markup=main_keyboard)

    #     await message_manager.track_message(message.chat.id, sent_message.message_id)
    #     await state.update_data(main_menu_message_id=sent_message.message_id)

    # @staticmethod
    # async def execute_back_to_start(callback: CallbackQuery, state: FSMContext, message_manager: MessageManager):
    #     """логика работы кноки 'Вернуться в начало'.

    #     Args:
    #         callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
    #         state: состояние памяти.
    #         message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    #     """
    #     await callback.answer("В начало.")
    #     chat_id = callback.message.chat.id
    #     message_id = callback.message.message_id
    #     text = "Вы вернулись в начало."

    #     # Очищаем все сообщения в чате
    #     # await message_manager.cleanup_chat_messages(callback.message.chat.id)

    #     await state.clear()
    #     is_admin_user = callback.from_user.id in ADMIN_IDS
    #     start_keyboard = kb.create_main_keyboard(is_admin_user)
    #     await message_manager.safe_edit_message(chat_id, message_id, text, start_keyboard)

    async def execute_back_to_start(self,
                                    callback: CallbackQuery,
                                    state: FSMContext,
                                    message_manager: MessageManager) -> None:
        """логика работы кнопки 'Вернуться в начало'.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: состояние памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        if await state.get_data() or await state.get_state():
            await state.clear()

        message_id = callback.message.message_id
        text = "Вы вернулись в начало."

        coffee_points = await self.get_coffee_points()
        # is_admin_user = callback.from_user.id in ADMIN_IDS
        # start_keyboard = create_main_keyboard_with_points(is_admin_user, coffee_points)
        main_keyboard = await self.get_main_keyboard(callback, coffee_points)

        await message_manager.safe_edit_message(self.chat_id, message_id, text, main_keyboard)

    async def get_coffee_point_info(self,
                                    callback: CallbackQuery,
                                    state: FSMContext,
                                    message_manager: MessageManager) -> None:
        """Получает подробную информацию о кофейной точке.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: состояние памяти.
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        await wait_typing(callback)

        msg = "Кофейная точка не найдена"

        message_id = callback.message.message_id

        point_id = int(callback.data.replace(CALLBACK_COFFEE_POINT_PREFIX, ""))

        await state.update_data(coffee_point_id=point_id)

        point_info = await self.get_coffee_point_info_from_db(point_id)

        if not point_info:
            await message_manager.safe_edit_message(self.chat_id, message_id, msg)
            return

        # Формируем сообщение с информацией о точке
        message_text = f"🏪 {point_info['name']}\n\n📍 Адрес: {point_info['address']}\n"
        if point_info["metro_station"]:
            message_text += f"🚇 Метро: {point_info['metro_station']}\n"

        point_keyboard = await self.collect_coffee_point_kb(point_id)

        await message_manager.safe_edit_message(self.chat_id,
                                                message_id,
                                                message_text,
                                                reply_markup=point_keyboard,
                                                parse_mode=ParseMode.MARKDOWN_V2)

    async def get_all_promotions(self,
                                 callback: CallbackQuery,
                                 message_manager: MessageManager) -> None:
        """Логика предоставления информации об акциях.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
        """
        text = """👋 *Дарим 5-й кофе бесплатно!* 🎉
        *Как участвовать:*
        1. Оплачивайте кофе банковской картой
            ⚠️ *Важно:* оплата по СБП не участвует в акции.

        *Сроки действия:*
            • Чтобы получить 5-й кофе бесплатно, купите 4 кофе в течение *365 дней* с момента первой покупки
            • Бесплатный кофе доступен в течение *30 дней* после оплаты 4-го кофе
        Ждём вас за вкусным кофе! ✨"""
        text = "Зима ❄️ близко, а акция еще ближе ☕️, ожидайте ❤️‍🔥"
        message_id = callback.message.message_id
        await message_manager.safe_edit_message(self.chat_id, message_id, text, back_to_start_keyboard)
