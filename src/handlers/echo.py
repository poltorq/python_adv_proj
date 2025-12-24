# src/handlers/echo.py
from aiogram import Router, F  # Изменённый импорт
from aiogram.types import Message
from src.lexicon.lexicon_ru import LEXICON_RU
from src.services.logger import setup_logger
from datetime import datetime
import random

router = Router()
logger = setup_logger(__name__)


@router.message()
async def echo_all(message: Message) -> None:
    """Обработчик всех текстовых сообщений"""
    user = message.from_user
    text = message.text
    if user is None or text is None:
        return

    logger.info(f"Пользователь {user.id} ({user.username}): {text}")
    await message.answer("Некорректный ввод")


# Декораторы исправлены с Text(...) на F.text == "..."
@router.message(F.text == "👋 Привет")  # Исправлено здесь
async def hello_button(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await message.answer(
        LEXICON_RU['hello_user'].format(name=user.first_name)
    )


@router.message(F.text == "📅 Дата")  # Исправлено здесь
async def date_button(message: Message) -> None:
    now = datetime.now()
    await message.answer(
        LEXICON_RU['current_date'].format(date=now.strftime('%d.%m.%Y %H:%M'))
    )


@router.message(F.text == "🎲 Случайное число")  # Исправлено здесь
async def random_button(message: Message) -> None:
    number = random.randint(1, 100)
    await message.answer(
        LEXICON_RU['random_number'].format(number=number)
    )


@router.message(F.text == "🆘 Помощь")  # Исправлено здесь
async def help_button(message: Message) -> None:
    await message.answer(LEXICON_RU['/help'])
