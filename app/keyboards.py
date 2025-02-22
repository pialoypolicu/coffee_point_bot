from typing import Literal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests.keyboards import IngredientNamesHint

TYPE_ITEM = Literal["drink_item_", "update_item_", "ingredient_item_"]
# drink_item_ - в случае просто перечисления меню напитков.
# ingredient_item_ - перечисление инггредиентов.
# update_item_ - в случае, когда нужно обновить напиток.


# возвращаемся в start.
back_to_start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Вернуться в начало", callback_data="back_to_start")]]
)

# кнопка назад, возвращает клиента к списку ингредиентов.
back_to_ingredients = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="ingredients")],
    ]
)

back_to_drinks = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Ингредиенты", callback_data="ingredients")],
        [InlineKeyboardButton(text="Назад", callback_data="drinks")],
    ]
)


def create_main_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """Создает главную инлайн клавиатуру, добавляя кнопку 'Admin' для админов."""
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="Напитки", callback_data="drinks"),
            InlineKeyboardButton(text="Контакты", callback_data="contacts"),
        ],
        [InlineKeyboardButton(text="Оставить отзыв/предложение", callback_data="feedback")],
    ]
    if is_admin:  # Добавляем кнопку Admin
        keyboard_buttons.append([InlineKeyboardButton(text="Admin", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def inline_builder(names: list[IngredientNamesHint], item: TYPE_ITEM = "drink_item_") -> InlineKeyboardMarkup:
    """Функция создает inline кнопки со списком напитков | ингредиентов.

    Последнее используется при создании напитка в БД.

    Args:
        names: список с наименованием ингридиентов.
        item: префикс к напиткам. Является составным строки для callback, префикс определяет действие.
    """
    keyboard = InlineKeyboardBuilder()
    for value in names:
        keyboard.add(InlineKeyboardButton(text=value["name"], callback_data=f"{item}{value['id']}"))
    keyboard.adjust(2)  # собирааем то что пришло из БД
    if item == "drink_item_":
        keyboard.row(back_to_start_keyboard.inline_keyboard[0][0])  # после отдельной строкой выводим кнопку на старт.
    elif item == "ingredient_item_":
        keyboard.row(back_to_drinks.inline_keyboard[1][0])
    else:
        # используется, когда добавляем ингредиенты к напиткам.
        keyboard.row(InlineKeyboardButton(text="Хватит", callback_data="update_item_stop"))
    return keyboard.as_markup()


# набор кнопок меню админа.
inline_admin_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="добавление игредиентов", callback_data="add_ingredient")],
        [InlineKeyboardButton(text="добавление напитка", callback_data="add_drink")],
        [back_to_start_keyboard.inline_keyboard[0][0]],
    ]
)

# клавиатура выбора типа ОС.
inline_feedback = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Предложение", callback_data="feedback_type:suggestion"),
            InlineKeyboardButton(text="Отзыв", callback_data="feedback_type:review"),
        ]
    ],
    row_width=2,
)
