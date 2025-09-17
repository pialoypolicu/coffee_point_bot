import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app import handlers as routers
from app.middlewares.base import activate_middlewares

load_dotenv()


async def main() -> None:
    bot = Bot(token=os.getenv("TG_TOKEN", "default"))
    dp = Dispatcher()

    dp.startup.register(startup)
    dp.include_routers(routers.admin_router, routers.feedback_router, routers.user_router, routers.ai_router)

    await dp.start_polling(bot)
    dp.shutdown.register(shutdown)

async def startup(dispatcher: Dispatcher) -> None:
    logging.info("start up ...")
    activate_middlewares(dispatcher, routers)

async def shutdown(dispatcher: Dispatcher) -> None:
    logging.info("Shutting down ...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
