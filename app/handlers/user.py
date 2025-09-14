from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.methods import EditMessageText
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

import app.keyboards as kb
from app.helpers import delete_messages, wait_typing
from app.logic.user_logic import UserLogic
from app.services.message_manager import MessageManager

user_router = Router()


@user_router.message(CommandStart())
async def command_start_points(message: Message,
                               state: FSMContext,
                               user_logic: UserLogic,
                               message_manager: MessageManager) -> None:
    """роутер команды /start.

    Args:
        message: объект сообщения.
        state: Состояния памяти.
        user_logic: логика работы с клиентом.
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await user_logic.execute_comand_start_show_points(message, state, message_manager)

@user_router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    """Роутер команды /help.

    Args:
        message: объект сообщения.
    """
    await wait_typing(message)
    await message.answer("Перейти в главное меню введите /start", reply_markup=ReplyKeyboardRemove())

@user_router.callback_query(F.data.startswith(kb.CALLBACK_COFFEE_POINT_PREFIX))
async def coffee_point_handler(callback: CallbackQuery,
                               user_logic: UserLogic,
                               message_manager: MessageManager) -> None:
    """Обработчик выбора кофейной точки. Т.е. нужно развернуть меню конкретной точки.

    Ars:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        user_logic: логика работы с клиентом.
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await user_logic.get_coffee_point_info(callback, message_manager)
    await message_manager.safe_callback_answer(callback)

@user_router.callback_query(F.data.startswith(kb.CALLBACK_DRINKS))
async def get_coffee_point_drinks(callback: CallbackQuery,
                                  state: FSMContext,
                                  user_logic: UserLogic,
                                  message_manager: MessageManager) -> None:
    """Роутер колбека кнопки Напитки. На выходе отдает все наитки, заккреленные за кофейней.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        user_logic: логика работы с клиентом.
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await user_logic.get_all_drinks(callback, state, message_manager)
    await message_manager.safe_callback_answer(callback, "Вы выбрали напитки.")


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
        await callback.bot.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                                     message_id=state_data["drink_msgs"]["desc_msg_id"],
                                                     reply_markup=kb.back_to_drinks)
        if not state_data.get("drink_msgs"):
            await state.clear()
    else:
        names = state_data.get("ingredients") or []
        await callback.message.edit_reply_markup(reply_markup=kb.inline_builder(names, item="ingredient_item_"))

@user_router.callback_query(F.data.startswith("drink_item_"))
async def drink_item_handler(callback: CallbackQuery,
                             state: FSMContext,
                             user_logic: UserLogic,
                             message_manager: MessageManager) -> None:
    """Роутер расскрывающий карточку напитка.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        user_logic: логика работы с клиентом.
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await user_logic.get_drink_detail(callback, state, message_manager)
    await callback.answer("Вы выбрали напиток")

@user_router.callback_query(F.data.startswith("ingredient_item_"))
async def ingredient_item_handler(callback: CallbackQuery, state: FSMContext, user_logic: UserLogic) -> None:
    """Роутер расскрывающий карточку ингредиента.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        user_logic: логика работы с клиентом.
    """
    await callback.answer("Вы выбрали ингредиент")
    await callback.message.edit_reply_markup()
    state_data = await state.get_data()
    if message_ids_to_delete := state_data.pop("ingredient_item_msgs_to_delete", None):
        await delete_messages(callback, message_ids_to_delete)
        await state.update_data(ingredient_item_msgs_to_delete=None)
        if not state_data.get("drink_msgs"):
            await state.clear()
    ingredient = await user_logic.get_igredient_photo(item_id=callback.data)
    photo_message = await callback.message.answer_photo(
        photo=ingredient["photos"][0]["photo_string"],
        caption=f"Ингредиент: {ingredient["name"]}",
        show_caption_above_media=True,
        )
    description_message = await callback.message.answer(text=f"Описание ингредиента: {ingredient["description"]}",
                                                        # reply_parameters={"message_id": photo_message.message_id},
                                                       reply_markup=kb.back_to_ingredients)
    await state.update_data(ingredient_item_msgs_to_delete=[photo_message.message_id, description_message.message_id])

@user_router.callback_query(F.data == "contacts")
async def get_contacts(callback: CallbackQuery, message_manager: MessageManager) -> None:
    """Роутер колбека кнопки Контакты.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        message_manager: Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await callback.answer("Вы выбрали контакты.")
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    contacts_text = "Эл. почта:\nstatsprofi-apetukhov@yandex.ru"
    await message_manager.safe_edit_message(chat_id, message_id, contacts_text, kb.back_to_start_keyboard)

# @user_router.callback_query(F.data == "back_to_start")
# async def back_to_start(
#         callback: CallbackQuery,
#         state: FSMContext,
#         user_logic: UserLogic,
#         message_manager: MessageManager,
#         ) -> None:
#     """Роутер колбека кнопки 'Назад в начало'.

#     Возвращает пользователя к стартовому меню.

#     Args:
#         callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
#         state: состояние памяти.
#         user_logic: логика работы с клиентом.
#         message_manager:Сервис для управления сообщениями с безопасной обработкой ошибок.
#     """
#     await user_logic.execute_back_to_start(callback, state, message_manager)
@user_router.callback_query(F.data == kb.CALLBACK_BACK_TO_START)
async def back_to_start(callback: CallbackQuery,
                        state: FSMContext,
                        user_logic: UserLogic,
                        message_manager: MessageManager) -> None:
    """Роутер колбека кнопки 'Назад в начало'.

    Возвращает пользователя к стартовому меню.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: состояние памяти.
        user_logic: логика работы с клиентом.
        message_manager:Сервис для управления сообщениями с безопасной обработкой ошибок.
    """
    await user_logic.execute_back_to_start(callback, state, message_manager)
    await message_manager.safe_callback_answer(callback, "В начало")
