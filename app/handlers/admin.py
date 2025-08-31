from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dotenv import load_dotenv

from app.configs import ADMIN_IDS
from app.database.requests.admin import IngredientHint, set_drink, set_ingredient
from app.database.requests.keyboards import get_names
from app.helpers import update_ingredient_ids
from app.keyboards import create_main_keyboard, inline_admin_menu, inline_builder
from app.states import Ingredient

load_dotenv()

admin_router = Router()


class Admin:
    def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


POSITION_TYPE = {"add_drink": "напитка", "add_ingredient": "игредиента"}


@admin_router.message(Admin(), Command(commands=["start"]), Ingredient())  # Ingredient.states указывает, что обработчик для всех состояний Ingredient
async def cancel_ingredient(message: Message, state: FSMContext) -> None:
    await state.clear()  # Сбрасываем состояние
    await message.answer("Оформление ингредиента прервано. Вы вернулись в начало.")

    is_admin_user = message.from_user.id in ADMIN_IDS  # Проверяем, является ли пользователь админом
    main_keyboard = create_main_keyboard(is_admin_user)  # Создаем клавиатуру динамически

    await message.answer("Добро пожаловать в Coffee Point!", reply_markup=main_keyboard)

@admin_router.callback_query(Admin(), F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery) -> None:
    await callback.answer("Вы выбрали Admin.")
    await callback.message.answer("Admin panel", reply_markup=inline_admin_menu)

@admin_router.callback_query(Admin(), F.data.in_(("add_ingredient", "add_drink")))
async def add_position(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    postition_type = POSITION_TYPE[callback.data]
    await state.update_data(postition_type=callback.data)
    await callback.answer(f"Вы выбрали добавление {postition_type}")
    await state.set_state(Ingredient.name)
    await callback.message.edit_text(f"Введите название {postition_type}.")

@admin_router.message(Admin(), Ingredient.name)
async def add_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(Ingredient.description)
    await message.answer("Введите описание.")

@admin_router.message(Admin(), Ingredient.description)
async def add_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(Ingredient.photo)
    await message.answer("Прикрепите фото.")

@admin_router.message(Admin(), Ingredient.photo, F.photo)
async def add_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo=message.photo[-1].file_id)
    state_data: IngredientHint = await state.get_data()
    if state_data["postition_type"] == "add_ingredient":
        await message.answer_photo(
            photo=state_data["photo"],
            caption=f"Название:{state_data["name"]}\nОписание:\n{state_data["description"][:100]}"
            )
        await state.clear()
        await set_ingredient(state_data)
        await message.answer("Admin panel", reply_markup=inline_admin_menu)
    else:
        await state.set_state(Ingredient.drink)
        await state.update_data(ingredient_ids=[])  # тут будем складывать уже добавленные ингредиенты к напитку.
        names = await get_names()
        await message.answer("Выберете ингридиенты.", reply_markup=inline_builder(names, "update_item_"))

@admin_router.callback_query(Admin(),
                             Ingredient.drink, F.data.startswith("update_item_") | F.data.startswith("update_stop"))
async def add_ingredient_fk(callback: CallbackQuery, state: FSMContext) -> None:
    ingredient_id: str = callback.data.split("_")[-1]
    state_data = await state.get_data()
    if ingredient_id != "stop":
        await state.set_state(Ingredient.drink)
        await state.update_data(ingredient_id=ingredient_id)
        without_ids = await update_ingredient_ids(state, int(ingredient_id))
        names = await get_names(without_ids=without_ids)
        await callback.message.answer("Выберете ингридиенты.", reply_markup=inline_builder(names, "update_item_"))
    else:
        await callback.message.answer_photo(
            photo=state_data["photo"],
            caption=f"Название напитка: {state_data["name"]}\nОписание:\n{state_data["description"][:100]}"
            )
        await state.clear()
        await set_drink(state_data)
        await callback.message.answer("Admin panel", reply_markup=inline_admin_menu)
