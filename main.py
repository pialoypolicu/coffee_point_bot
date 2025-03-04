import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.database.base import async_main
from app.handlers.admin import admin_router
from app.handlers.feedback import feedback_router
from app.handlers.user import user_router
from app.logger import Logger
from app.middlewares.logger_middleware import LoggingMiddleware

load_dotenv()


async def main() -> None:
    bot = Bot(token=os.getenv("TG_TOKEN", "default"))
    dp = Dispatcher()
    logger = Logger()

    dp.callback_query.middleware(LoggingMiddleware(logger))
    dp.message.middleware(LoggingMiddleware(logger))
    dp.include_routers(admin_router, user_router, feedback_router)
    dp.startup.register(startup)

    await dp.start_polling(bot)
    dp.shutdown.register(shutdown)

async def startup(dispatcher: Dispatcher) -> None:
    logging.info("start up ...")
    await async_main()

async def shutdown(dispatcher: Dispatcher) -> None:
    logging.info("Shutting down ...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
