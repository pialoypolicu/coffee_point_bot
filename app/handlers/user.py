import asyncio
from random import random

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

import app.keyboards as kb
from app.database.models import Drink
from app.database.requests.keyboards import get_names
from app.database.requests.user import UserDataHint, get_drink, get_igredient_photo, set_user
from app.handlers.admin import ADMIN_IDS
from app.helpers import delete_messages

user_router = Router()


async def wait_typing(message: Message) -> None:
    if (bot := message.bot) and (user := message.from_user):
        await bot.send_chat_action(chat_id=user.id,
                                        action=ChatAction.TYPING)
        await asyncio.sleep(random())

@user_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """роутер команды /start.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
    """
    if await state.get_data():
        await state.clear()
    await wait_typing(message)
    user_data: UserDataHint = {"tg_id": message.from_user.id,
                               "tg_username": message.from_user.username,
                               "first_name": message.from_user.first_name,
                               "full_name": message.from_user.full_name,
                               "last_name": message.from_user.last_name,
                               "been_deleted": False}
    await set_user(user_data)

    is_admin_user = message.from_user.id in ADMIN_IDS  # Проверяем, является ли пользователь админом
    main_keyboard = kb.create_main_keyboard(is_admin_user)  # Создаем клавиатуру динамически

    await message.answer("Добро пожаловать в Coffee Point!", reply_markup=main_keyboard)

@user_router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    """Роутер команды /help.

    Args:
        message: объект сообщения.
    """
    await wait_typing(message)
    await message.answer("Перейти в главное меню введите /start", reply_markup=ReplyKeyboardRemove())

@user_router.callback_query(F.data == "drinks")
async def drinks(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер колбека кнопки Напитки.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    await callback.answer("Вы выбрали напитки.")
    state_data = await state.get_data()
    if message_ids_to_delete := state_data.get("item_msgs_to_delete"):
        await delete_messages(callback, message_ids_to_delete)
        await state.clear()
    else:
        names = await get_names(model=Drink)
        await callback.message.edit_text("Выберете напиток", reply_markup=kb.inline_builder(names))

@user_router.callback_query(F.data == "ingredients")
async def ingredients(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер колбека кнопки Напитки.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    await callback.answer("Вы выбрали Ингредиенты.")
    state_data = await state.get_data()
    if message_ids_to_delete := state_data.pop("ingredient_item_msgs_to_delete", None):
        await state.update_data(ingredient_item_msgs_to_delete=None)
        await delete_messages(callback, message_ids_to_delete)
        if not state_data.get("item_msgs_to_delete"):
            await state.clear()
    else:
        names = state_data["ingredients"]
        await callback.message.edit_text("Выберете ингредиент",
                                         reply_markup=kb.inline_builder(names, item="ingredient_item_"))

@user_router.callback_query(F.data.startswith("drink_item_"))
async def drink_item_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер рассккрывающий карточку напитка.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    await callback.answer("Вы выбрали напиток")
    state_data = await state.get_data()
    if message_ids_to_delete := state_data.get("item_msgs_to_delete"):
        await delete_messages(callback, message_ids_to_delete)
        await state.clear()
    result = await get_drink(item_id=callback.data)
    await state.update_data(ingredients=result["ingredients"])
    photo_message = await callback.message.answer_photo(
        photo=result["photos"][0]["photo_string"],
        caption=f"Напиток: {result["name"]}",
        show_caption_above_media=True,
        )
    description_message = await callback.message.answer(text=f"Описание напитка: {result["description"]}",
                                                       reply_parameters={"message_id": photo_message.message_id},
                                                       reply_markup=kb.back_to_drinks)
    await state.update_data(item_msgs_to_delete=[photo_message.message_id, description_message.message_id])

@user_router.callback_query(F.data.startswith("ingredient_item_"))
async def ingredient_item_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер расскрывающий карточку ингредиента.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
    """
    await callback.answer("Вы выбрали ингредиент")
    state_data = await state.get_data()
    if message_ids_to_delete := state_data.pop("ingredient_item_msgs_to_delete", None):
        await delete_messages(callback, message_ids_to_delete)
        await state.update_data(ingredient_item_msgs_to_delete=None)
        if not state_data.get("item_msgs_to_delete"):
            await state.clear()
    ingredient = await get_igredient_photo(item_id=callback.data)
    photo_message = await callback.message.answer_photo(
        photo=ingredient["photos"][0]["photo_string"],
        caption=f"Ингредиент: {ingredient["name"]}",
        show_caption_above_media=True,
        )
    description_message = await callback.message.answer(text=f"Описание ингредиента: {ingredient["description"]}",
                                                        reply_parameters={"message_id": photo_message.message_id},
                                                       reply_markup=kb.back_to_ingredients)
    await state.update_data(ingredient_item_msgs_to_delete=[photo_message.message_id, description_message.message_id])

@user_router.callback_query(F.data == "contacts")
async def get_contacts(callback: CallbackQuery) -> None:
    """Роутер колбека кнопки Контакты.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
    """
    await callback.answer("Вы выбрали контакты.")
    contacts_text = "Эл. почта:\nstatsprofi-apetukhov@yandex.ru"
    await callback.message.answer(contacts_text, reply_markup=kb.back_to_start_keyboard)

@user_router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Роутер колбека кнопки 'Назад в начало'.

    Возвращает пользователя к стартовому меню.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: состояние памяти.
    """
    await callback.answer("В начало.")
    await state.clear()
    is_admin_user = callback.from_user.id in ADMIN_IDS
    start_keyboard = kb.create_main_keyboard(is_admin_user)
    await callback.message.answer("Вы вернулись в начало.", reply_markup=start_keyboard)
