from aiogram import Router, types
from aiogram.filters import Command
import os

router = Router()

SERVER_URL = "http://turbomuza.ru"

@router.message(Command("auth"))
async def auth_handler(message: types.Message):
    telegram_id = message.from_user.id
    chat_id = message.chat.id

    url = f"{SERVER_URL}/auth/google?user_id={telegram_id}&chat_id={chat_id}"

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🔐 Авторизоваться через Google", url=url)]
        ]
    )

    await message.answer(
        "Для работы с Google Calendar нужно авторизоваться 👇", reply_markup=keyboard
    )
