from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from openai import AsyncOpenAI

from app.helpers import get_moscow_time, wait_typing
from app.keyboards import back_to_start_keyboard


class AIGeneratorLogic:
    """класс логики для взаимодействия с openai."""

    def __init__(self, ai_client: AsyncOpenAI):
        """конструктор объекта, для взаимодействия с openia.

        Args:
            ai_client: клиент.
        """
        self.ai_client = ai_client

    async def gpt_text(self, callback: CallbackQuery, state: FSMContext) -> None:
        """Функция отправляет сообщение к ИИ для запроса отличного дня.

        Args:
            callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
            state: Состояния памяти.
        """
        await wait_typing(callback)
        msc_time = get_moscow_time()
        msg_for_chat = ("Доброе пожелание, на русском языке, человеку, который любит кофе. "
                        "Пожелание обезличенно, так как не изветно, это будет читать мужчина или женщина. "
                        "Не более 200 символов и сразу выдай финальный ответ. "
                        "ВАЖНО, клиент ддолжен лолучить чистый текст, без своих технических дополнений от себя!"
                        f"Учитывай время: сейчас {msc_time}, от этого зависит в ответе исользуем утро, день или вечер. "
                        "Используй markdown для приложения teleram")
        completion = await self.ai_client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": msg_for_chat,
                }],
            model="deepseek/deepseek-r1-0528:free",
            )
        text = completion.choices[0].message.content
        await callback.message.delete()  # удаляем сообщение от генерируемое функцией create_main_keyboard
        message_for_user = await callback.message.answer(
            text,
            reply_markup=back_to_start_keyboard,
            parse_mode=ParseMode.MARKDOWN,
            )
        await state.update_data(msg_for_delete=[message_for_user.message_id])
