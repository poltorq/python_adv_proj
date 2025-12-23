import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from src.services.logger import setup_logger
from src.handlers import routers


# Настройка
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в .env файле!")

logger = setup_logger(__name__)


async def main() -> None:
    """Основная функция запуска бота"""
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Регистрируем роутеры
    for router in routers:
        dp.include_router(router)

    # Запускаем бота
    logger.info("🚀 Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
