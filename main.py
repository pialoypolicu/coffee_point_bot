import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from app.database.base import async_main
from app.handlers.admin import admin_router
from app.handlers.feedback import feedback_router
from app.handlers.user import user_router

load_dotenv()


async def main():
    bot = Bot(token=os.getenv("TG_TOKEN", "default"))
    dp = Dispatcher()
    dp.include_routers(admin_router, user_router, feedback_router)
    dp.startup.register(startup)
    await dp.start_polling(bot)
    dp.shutdown.register(shutdown)

async def startup(dispatcher: Dispatcher):
    logging.info("start up ...")
    await async_main()

async def shutdown(dispatcher: Dispatcher):
    logging.info("Shutting down ...")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
