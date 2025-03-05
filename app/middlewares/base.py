from typing import Any, Protocol

from aiogram import Dispatcher, Router

from app.logger import Logger
from app.logic.feedback import LogicFeedback
from app.logic.user_logic import UserLogic
from app.middlewares.feedback import LogicFeedbackMiddleware
from app.middlewares.logger_middleware import LoggingMiddleware
from app.middlewares.user_middleware import UserLogickMiddleware


class RoutersModule(Protocol):
    """Хинт модуля handlers/__init__.py."""

    admin_router: Router
    user_router: Router
    feedback_router: Router


logger = Logger()
logic_feedback = LogicFeedback()
user_logic = UserLogic()


def activate_middlewares(dp: Dispatcher, routers: Any) -> None:
    """Активируем прослоечки нашего бота.

    Args:
        dp: диспетчер, обработчик сообщений.
        routers: модуль handlerrrs/__init__.py который содержит все роутеры бота.
    """
    routers.feedback_router.message.middleware(LogicFeedbackMiddleware(logic_feedback))
    routers.feedback_router.callback_query.middleware(LogicFeedbackMiddleware(logic_feedback))

    routers.user_router.message.middleware(UserLogickMiddleware(user_logic))
    routers.user_router.callback_query.middleware(UserLogickMiddleware(user_logic))

    dp.callback_query.middleware(LoggingMiddleware(logger))
    dp.message.middleware(LoggingMiddleware(logger))
