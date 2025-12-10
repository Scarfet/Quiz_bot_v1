# bot/main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher

from .config import API_TOKEN
from .handlers import router
from .db import init_db


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()

    # регистрируем все хендлеры
    dp.include_router(router)

    # инициализируем базу
    await init_db()

    # запускаем бота
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
