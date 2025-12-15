from aiogram import Router, types
from aiogram.filters import Command
from src.lexicon.lexicon_ru import LEXICON_RU
from src.keyboards.keyboards import get_main_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user = message.from_user
    await message.answer(
        LEXICON_RU['/start'].format(name=user.first_name),
        reply_markup=get_main_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(LEXICON_RU['/help'])


@router.message(Command("echo"))
async def cmd_echo(message: types.Message):
    """Обработчик команды /echo"""
    text = message.text[6:].strip()  # убираем "/echo "

    if not text:
        await message.answer(LEXICON_RU['echo_empty'])
        return

    await message.answer(LEXICON_RU['echo_response'].format(text=text))