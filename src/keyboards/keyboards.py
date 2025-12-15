from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👋 Привет"), KeyboardButton(text="📅 Дата")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="🎲 Случайное число")]
        ],
        resize_keyboard=True
    )

def get_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline клавиатура"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Сайт", url="https://google.com")],
            [
                InlineKeyboardButton(text="✅ Да", callback_data="yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="no")
            ]
        ]
    )