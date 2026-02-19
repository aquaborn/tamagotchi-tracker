import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Create Bot instance with default properties
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create Dispatcher
    dp = Dispatcher()

    # Register handlers
    from handlers.start import router as start_router
    dp.include_router(start_router)
    
    try:
        logging.info("Bot is starting...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped!")