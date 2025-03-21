from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.database.requests.admin import DrinkHint


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
