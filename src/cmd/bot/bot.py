import asyncio
import os
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from src.services.logger import setup_logger  # type: ignore
from src.handlers import routers  # type: ignore

# Добавляем путь к корню проекта для импорта model
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Настройка
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден в .env файле!")

logger = setup_logger(__name__)


async def main() -> None:
    """Основная функция запуска бота"""
    # Предзагрузка NER модели
    try:
        from model import get_pipeline
        logger.info("🧠 Загрузка NER модели...")
        get_pipeline()
        logger.info("✅ NER модель загружена")
    except Exception as e:
        logger.warning(f"⚠️ NER модель не загружена: {e}")
    
    # Создаем объекты
    bot = Bot(token=TOKEN)  # type: ignore
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
