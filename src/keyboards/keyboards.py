from datetime import datetime, timedelta
import calendar
from typing import Optional

from aiogram.types import (ReplyKeyboardMarkup,
                           KeyboardButton,
                           InlineKeyboardMarkup,
                           InlineKeyboardButton)





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


def get_auth_keyboard(some_url: str) -> InlineKeyboardMarkup:
    """Here we request the authorisation"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Авторизоваться", url=some_url), ]
        ]
    )


def get_mode_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard для выбора режима события"""
    keyboard = [
        [InlineKeyboardButton(text="Классический режим",
                              callback_data="mode_no_ai"),
         InlineKeyboardButton(text="AI режим",
                              callback_data="mode_ai")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_calendar_keyboard(
        year: Optional[int] = None,
        month: Optional[int] = None
) -> InlineKeyboardMarkup:
    """Inline keyboard for choosing the calendar options"""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_days = cal.monthdayscalendar(year, month)

    keyboard: list[list[InlineKeyboardButton]] = []

    """Month display"""
    keyboard.append([
        InlineKeyboardButton(
            text=f"{calendar.month_name[month]} {year}",
            callback_data="ignore"
        )
    ])

    """Days of the week display"""
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="ignore")
        for day in week_days
    ])

    """Days of the month display"""
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(
                    InlineKeyboardButton(text=" ", callback_data="ignore")
                )
            else:
                # TEMP i'll fix it later
                row.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f"date_{year}_{month}_{day}"
                    )
                )
        keyboard.append(row)

    """Months navigation"""
    prev_month = datetime(year, month, 1) - timedelta(days=1)
    next_month = datetime(
        year, month,
        calendar.monthrange(year, month)[1]) + timedelta(days=1)

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"month_{prev_month.year}_{prev_month.month}"
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"month_{next_month.year}_{next_month.month}"
        )
    ])

    keyboard.append([InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_time_hour_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for choosing the time options"""
    # TEMP right now that's kind of ugly sorry
    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for hour in range(24):
        row.append(InlineKeyboardButton(
            text=str(hour),
            callback_data=f"time_{hour}"))
        if (hour + 1) % 6 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_time_minute_keyboard(hour: int) -> InlineKeyboardMarkup:
    """Inline keyboard for choosing the time options"""
    # TEMP right now that's kind of ugly sorry
    keyboard: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for minute in range(0, 60, 5):
        row.append(InlineKeyboardButton(
            text=f"{minute:02}",
            callback_data=f"time_{hour}:{minute}"))
        if (len(row)) % 6 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="⬅️", callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_duration_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for choosing the duration options"""
    durations = [30, 60, 90, 120]
    keyboard: list[list[InlineKeyboardButton]] = []
    for d in durations:
        keyboard.append([InlineKeyboardButton(
            text=f"{d} мин",
            callback_data=f"duration_{d}")])

    keyboard.append([InlineKeyboardButton(text="⬅️", callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard for choosing the confirmation options"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no"),
            InlineKeyboardButton(text="⬅️", callback_data="back")
        ]
    ])

def get_add_another_event_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="➕ Добавить ещё одно событие",
                callback_data="add_another_event"
            )
        ]
    ])

def get_ai_back_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопка возврата из AI режима
    к выбору режима события.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="ai_back"
                )
            ]
        ]
    )