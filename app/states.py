from aiogram.fsm.state import State, StatesGroup


class Ingredient(StatesGroup):
    name = State()
    description = State()
    photo = State()
    drink = State()

class FeedBack(StatesGroup):
    name = State()
    contact = State()
    text = State()


# Определение состояний формы
class FeedbackForm(StatesGroup):
    waiting_for_name = State()
    # waiting_for_phone = State()
    waiting_for_feedback_type = State()
    waiting_for_text = State()
    photo = State()
