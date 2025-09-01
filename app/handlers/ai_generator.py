from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.logic.ai_gen_logic import AIGeneratorLogic

ai_router = Router()


@ai_router.callback_query(F.data == "good_wish")
async def ai_gen_wish(callback: CallbackQuery, state: FSMContext, aigen_logic: AIGeneratorLogic) -> None:
    """Роутер колбека кнопки Отличного дня!.

    Args:
        callback: объект входящий запрос колбека кнопки обратного вызова на inline keyboard
        state: Состояния памяти.
        aigen_logic: логика для генерации сообщений к ИИ. Объект прилетает из AIGenLogicMiddleware.
    """
    await callback.answer("🔄 Генерирую пожелание... Это займет несколько секунд")
    # Меняем текст сообщения
    await callback.message.edit_text(
        "✨ Генерирую особенное пожелание для тебя...",
        reply_markup=None
    )
    try:
        await aigen_logic.gpt_text(callback, state)
    except Exception:
        # В случае ошибки показываем сообщение
        await callback.message.edit_text(
            "❌ Произошла ошибка при генерации. Попробуй еще раз!"
        )
        raise
