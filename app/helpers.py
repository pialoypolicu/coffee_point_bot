import asyncio
import random
from datetime import datetime

import pytz
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.requests.admin import DrinkHint

MOSCOW_TZ = pytz.timezone("Europe/Moscow")  # кеширование часового пояса.


async def delete_messages(callback: CallbackQuery, msg_ids_fro_delete: list[int]) -> None:
    """Функция удаляет сообщения по id сообщения и подчищает состояние state.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        msg_ids_fro_delete: список id сообщений.
    """
    for message_id in msg_ids_fro_delete:
        await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=message_id)

async def update_ingredient_ids(state: FSMContext, ingredient_id: int) -> list[int]:
    """обновляем значение ingredient_ids. в список добавляем id ингридиентов, которые мы добавили к напитку.

    Args:
        state: Состояния памяти.
        ingredient_id: id ингридиента.

    Returns:
        list[int]: _description_
    """
    data: DrinkHint = await state.get_data()
    data["ingredient_ids"].append(ingredient_id)
    await state.update_data(ingredient_ids=data["ingredient_ids"])
    return data["ingredient_ids"]

def get_moscow_time() -> str:
    """Получить московское время, в формате 'hh:mm'."""
    moscow_time = datetime.now(MOSCOW_TZ)
    return moscow_time.strftime("%H:%M")

async def wait_typing(message: Message | CallbackQuery) -> None:
    """функция вызывает поп-ап 'Печатает'.

    Args:
        message: объект сообщения или колбека.
    """
    if (bot := message.bot) and (user := message.from_user):
        await bot.send_chat_action(chat_id=user.id,
                                        action=ChatAction.TYPING)
        await asyncio.sleep(random.uniform(0.1, 0.5))
