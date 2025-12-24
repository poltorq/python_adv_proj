import calendar
from datetime import datetime

from aiogram.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)

from src.keyboards.keyboards import (
    get_main_keyboard,
    get_inline_keyboard,
    get_auth_keyboard,
    get_mode_keyboard,
    get_calendar_keyboard,
    get_time_hour_keyboard,
    get_time_minute_keyboard,
    get_duration_keyboard,
    get_confirmation_keyboard,
)


def test_get_main_keyboard():
    kb = get_main_keyboard()

    assert isinstance(kb, ReplyKeyboardMarkup)
    assert len(kb.keyboard) == 2
    assert kb.keyboard[0][0].text == "👋 Привет"
    assert kb.keyboard[0][1].text == "📅 Дата"


def test_get_inline_keyboard():
    kb = get_inline_keyboard()

    assert isinstance(kb, InlineKeyboardMarkup)
    assert kb.inline_keyboard[0][0].url == "https://google.com"
    assert kb.inline_keyboard[1][0].callback_data == "yes"
    assert kb.inline_keyboard[1][1].callback_data == "no"


def test_get_auth_keyboard():
    url = "https://example.com/auth"
    kb = get_auth_keyboard(url)

    assert isinstance(kb, InlineKeyboardMarkup)
    assert kb.inline_keyboard[0][0].url == url
    assert kb.inline_keyboard[0][0].text == "Авторизоваться"


def test_get_mode_keyboard():
    kb = get_mode_keyboard()

    buttons = kb.inline_keyboard
    assert buttons[0][0].callback_data == "mode_no_ai"
    assert buttons[0][1].callback_data == "mode_ai"
    assert buttons[1][0].callback_data == "back"


def test_get_calendar_keyboard_structure():
    year, month = 2024, 5
    kb = get_calendar_keyboard(year, month)

    assert isinstance(kb, InlineKeyboardMarkup)
    assert calendar.month_name[month] in kb.inline_keyboard[0][0].text
    assert len(kb.inline_keyboard[1]) == 7  # days of week


def test_get_calendar_keyboard_contains_dates():
    kb = get_calendar_keyboard(2024, 1)

    date_buttons = [
        btn
        for row in kb.inline_keyboard
        for btn in row
        if btn.callback_data and btn.callback_data.startswith("date_")
    ]

    assert any("date_2024_1_1" in btn.callback_data for btn in date_buttons)


def test_get_time_hour_keyboard():
    kb = get_time_hour_keyboard()

    assert isinstance(kb, InlineKeyboardMarkup)

    hour_buttons = [
        btn for row in kb.inline_keyboard[:-1] for btn in row
    ]

    assert len(hour_buttons) == 24
    assert hour_buttons[0].callback_data == "time_0"
    assert hour_buttons[-1].callback_data == "time_23"


def test_get_time_minute_keyboard():
    kb = get_time_minute_keyboard(10)

    minute_buttons = [
        btn for row in kb.inline_keyboard[:-1] for btn in row
    ]

    assert minute_buttons[0].callback_data == "time_10:0"
    assert minute_buttons[1].text == "05"
    assert len(minute_buttons) == 12


def test_get_duration_keyboard():
    kb = get_duration_keyboard()

    durations = [btn.callback_data for row in kb.inline_keyboard[:-1] for btn in row]
    assert durations == [
        "duration_30",
        "duration_60",
        "duration_90",
        "duration_120",
    ]


def test_get_confirmation_keyboard():
    kb = get_confirmation_keyboard()

    callbacks = [btn.callback_data for btn in kb.inline_keyboard[0]]
    assert callbacks == ["confirm_yes", "confirm_no", "back"]
