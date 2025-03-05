from aiogram.fsm.context import FSMContext
from aiogram.methods import EditMessageText
from aiogram.types import CallbackQuery

from app.database.models import Drink
from app.database.requests.keyboards import get_names
from app.database.requests.user import UserContext
from app.helpers import delete_messages
from app.keyboards import back_to_drinks, inline_builder


class UserLogic(UserContext):
    """класс логики для взаимодействия клиента с ботом."""

    async def get_all_drinks(self, callback: CallbackQuery, state: FSMContext) -> EditMessageText | None:
        state_data = await state.get_data()
        if message_ids_to_delete := state_data.get("drink_msgs"):  # назад к списку напитков.
            await delete_messages(callback, [message_ids_to_delete["photo_msg_id"]])
            await state.clear()
        names = await get_names(model=Drink)
        return await callback.message.edit_text("Выберете напиток", reply_markup=inline_builder(names))

    async def get_drink_info(self, callback: CallbackQuery, state: FSMContext) -> None:
        state_data = await state.get_data()
        if message_ids_to_delete := state_data.get("drink_msgs"):  # возвращаемся к списку напитков.
            await delete_messages(callback, list(message_ids_to_delete.values()))
            await state.clear()
        result = await self.get_drink(item_id=callback.data)
        await state.update_data(ingredients=result["ingredients"])
        await callback.message.delete()
        photo_message = await callback.message.answer_photo(
            photo=result["photos"][0]["photo_string"],
            caption=f"Напиток: {result["name"]}",
            show_caption_above_media=True,
            )
        description_message = await callback.message.answer(text=f"Описание напитка: {result["description"]}",
                                                            reply_markup=back_to_drinks)
        await state.update_data(drink_msgs={"photo_msg_id": photo_message.message_id,
                                            "desc_msg_id": description_message.message_id},
                                ingredients=result["ingredients"])
