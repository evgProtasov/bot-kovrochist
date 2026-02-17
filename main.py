import asyncio
from aiogram import Dispatcher
from app.handlers import router
from app.bot.bot import bot

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())