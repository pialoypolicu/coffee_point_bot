from typing import Literal, Required, TypedDict

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.requests.keyboards import IngredientNamesHint
from app.database.requests.user import CoffeePointHint

TYPE_ITEM = Literal["drink_item_", "update_item_", "ingredient_item_"]
# drink_item_ - в случае просто перечисления меню напитков.
# ingredient_item_ - перечисление инггредиентов.
# update_item_ - в случае, когда нужно обновить напиток.

# Константы для callback_data для избежания опечаток
# TODO: вынести в ENUM + вынести в отдельный менеджер логику создания клавиатур.
CALLBACK_BACK_TO_START = "back_to_start"
CALLBACK_INGREDIENTS = "ingredients"
CALLBACK_DRINKS = "drinks_coffee_point_"
CALLBACK_SEND_REVIEW = "send_review"
CALLBACK_ADMIN_PANEL = "admin_panel"
CALLBACK_ADD_INGREDIENT = "add_ingredient"
CALLBACK_ADD_DRINK = "add_drink"
CALLBACK_UPDATE_ITEM_STOP = "update_item_stop"
CALLBACK_FEEDBACK_SUGGESTION = "feedback_type:suggestion"
CALLBACK_FEEDBACK_REVIEW = "feedback_type:review"
CALLBACK_CONTACTS = "contacts"
CALLBACK_GOOD_WISH = "good_wish"
CALLBACK_FEEDBACK = "feedback"
CALLBACK_COFFEE_POINTS = "coffee_points"
CALLBACK_COFFEE_POINT_PREFIX = "coffee_point_"
CALLBACK_ITEM_PREFIX = "drink_item_"

class PrevStep(TypedDict):
    """Хинт набора данных для создания какстомной кнопки."""

    text: Required[str]
    callback_data: Required[str]

def create_main_keyboard_with_points(is_admin: bool, coffee_points: list[CoffeePointHint]) -> InlineKeyboardMarkup:
    """Создает главную инлайн клавиатуру с учетом кофейных точек."""
    inline_builder = InlineKeyboardBuilder()

    inline_builder.row(
        InlineKeyboardButton(text="Отличного дня!", callback_data=CALLBACK_GOOD_WISH),
        InlineKeyboardButton(text="Контакты", callback_data="contacts"),
        )

    # Кнопки кофейных точек (максимум 2 в строке)
    for point in coffee_points:
        point_text = f"{point['name']}"
        if point["metro_station"]:
            point_text += f" ({point['metro_station']})"
        inline_builder.row(InlineKeyboardButton(
            text=point_text,
            callback_data=f"{CALLBACK_COFFEE_POINT_PREFIX}{point['id']}"
        ))

    # Кнопка админа, если пользователь является админом
    if is_admin:
        inline_builder.row(InlineKeyboardButton(text="Admin", callback_data=CALLBACK_ADMIN_PANEL))

    return inline_builder.as_markup()

def create_custom_inlline_button(callback_data: str, text: str = "Назад") -> InlineKeyboardButton:
    """Функция динамически создает inline кноку.

    Args:
        callback_data: строка, путь до роутера.
        text: текст кноки. Defaults to "Назад".
    """
    return InlineKeyboardButton(text=text, callback_data=callback_data)


# возвращаемся в start.
back_to_start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Вернуться в начало", callback_data=CALLBACK_BACK_TO_START)]]
)
back_to_start_or_send_review_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Отправить без фото", callback_data=CALLBACK_SEND_REVIEW)],
        [back_to_start_keyboard.inline_keyboard[0][0]],
    ]
)

# кнопка назад, возвращает клиента к списку ингредиентов.
back_to_ingredients = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="ingredients")],
    ]
)

async def make_back_to_drinks_kb(point_id: int) -> InlineKeyboardMarkup:
    """создание inline кноки назад.

    Args:
        point_id: ID кофейной точки.
    """
    callback_data = f"{CALLBACK_DRINKS}{point_id}"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data=callback_data)]])
# back_to_drinks = InlineKeyboardMarkup(
#     inline_keyboard=[
#         # [InlineKeyboardButton(text="Ингредиенты", callback_data="ingredients")],
#         [InlineKeyboardButton(text="Назад", callback_data="drinks")],
#     ]
# )

def create_main_keyboard(is_admin: bool) -> InlineKeyboardMarkup:
    """Создает главную инлайн клавиатуру, добавляя кнопку 'Admin' для админов."""
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="Напитки", callback_data="drinks"),
            # InlineKeyboardButton(text="Контакты", callback_data="contacts"),
        ],
        [InlineKeyboardButton(text="Отличного дня!", callback_data="good_wish")],
        [InlineKeyboardButton(text="Оставить отзыв/предложение", callback_data="feedback")],
    ]
    if is_admin:  # Добавляем кнопку Admin
        keyboard_buttons.append([InlineKeyboardButton(text="Admin", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def create_point_keyboard(point_id: int, prev_step: PrevStep | None) -> InlineKeyboardMarkup:
    """Создает главную инлайн клавиатуру, добавляя кнопку 'Admin' для админов."""
    keyboard_buttons = [
        [
            InlineKeyboardButton(text="Напитки", callback_data=f"{CALLBACK_DRINKS}{point_id}"),
            # InlineKeyboardButton(text="Контакты", callback_data="contacts"),
        ],
        [InlineKeyboardButton(text="Оставить отзыв/предложение", callback_data="feedback")],
    ]
    if prev_step:
        button = [InlineKeyboardButton(text=prev_step["text"], callback_data=prev_step["callback_data"])]
        keyboard_buttons.append(button)
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def inline_builder(names: list[IngredientNamesHint],
                   item: TYPE_ITEM = "drink_item_",
                   prev_callback_data: str | None = None,
                   prev_text: str = "Назад") -> InlineKeyboardMarkup:
    """Функция создает inline кнопки со списком напитков | ингредиентов.

    Последнее используется при создании напитка в БД.

    Args:
        names: список с наименованием ингридиентов.
        item: префикс к напиткам. Является составным строки для callback, префикс определяет действие.
        prev_callback_data: callback_data, путь который отловит хендлер.
        prev_text: текст кнпоки.
    """
    inline_builder = InlineKeyboardBuilder()
    for value in names:
        inline_builder.add(InlineKeyboardButton(text=value["name"], callback_data=f"{item}{value['id']}"))
    inline_builder.adjust(2)  # собирааем то что пришло из БД
    # if item == "drink_item_":
    #     inline_button = 
    #     keyboard.row(back_to_start_keyboard.inline_keyboard[0][0])  # после отдельной строкой выводим кнопку на старт.
    # # elif item == "ingredient_item_":
    # #     keyboard.row(back_to_drinks.inline_keyboard[1][0])
    # else:
    #     # используется, когда добавляем ингредиенты к напиткам.
    #     keyboard.row(InlineKeyboardButton(text="Хватит", callback_data="update_item_stop"))
    if prev_callback_data:
        callback_data_button = create_custom_inlline_button(callback_data=prev_callback_data, text=prev_text)
        inline_builder.row(callback_data_button)

    return inline_builder.as_markup()


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
        ],
            [back_to_start_keyboard.inline_keyboard[0][0]],
    ],
    row_width=2,
)
