from aiogram.fsm.state import State, StatesGroup


class Ingredient(StatesGroup):
    name = State()
    description = State()
    photo = State()
    drink = State()


# Определение состояний формы
class FeedbackForm(StatesGroup):
    waiting_for_name = State()
    waiting_score = State()
    waiting_for_feedback_type = State()
    waiting_for_text = State()
    waiting_text_for_admin = State()
    photo = State()
