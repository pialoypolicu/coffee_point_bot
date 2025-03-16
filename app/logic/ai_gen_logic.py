from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from openai import AsyncOpenAI

from app.keyboards import back_to_start_keyboard


class AIGeneratorLogic:
    """класс логики для взаимодействия с openai."""

    def __init__(self, ai_client: AsyncOpenAI):
        self.ai_client = ai_client

    async def gpt_text(self, callback: CallbackQuery, state: FSMContext) -> None:
        """Функция отправляет сообщение к ИИ для запроса отличного дня.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
        """
        completion = await self.ai_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": "Доброе пожелание на день, человеку, который любит кофе. Пожелание обезличенно, так как не изветно, это будет читать мужчина или женщина. Не более 200 символов",
                }],
            model="deepseek/deepseek-chat",
            )
        text = completion.choices[0].message.content
        await callback.message.delete()  # удаляем сообщение от генерируемое фуункцией create_main_keyboard

        message_for_user = await callback.message.answer(text, reply_markup=back_to_start_keyboard)
        await state.update_data(msg_for_delete=[message_for_user.message_id])
