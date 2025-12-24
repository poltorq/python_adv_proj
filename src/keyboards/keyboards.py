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
    """Главное меню с кнопками"""
    keyboard = [
        [
            InlineKeyboardButton(text="Классический режим", callback_data="mode_no_ai"),
            InlineKeyboardButton(text="AI режим", callback_data="mode_ai")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить событие", callback_data="cmd_delete_event"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back")
        ]
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


def get_calendar_list_keyboard(calendars: list) -> InlineKeyboardMarkup:
    """Клавиатура для выбора календаря из списка"""
    keyboard = []

    for idx, cal in enumerate(calendars, 1):
        text = f"{idx}. {cal.get('summary', 'Без названия')}"
        if cal.get('primary'):
            text = f"⭐ {text}"

        keyboard.append([
            InlineKeyboardButton(
                text=text[:50],
                callback_data=f"select_calendar_{cal['id']}"
            )
        ])

    # Добавляем кнопки действий
    keyboard.append([
        InlineKeyboardButton(text="➕ Новый календарь", callback_data="new_calendar_action"),
        InlineKeyboardButton(text="🗑 Удалить календарь", callback_data="delete_calendar_action")
    ])

    keyboard.append([
        InlineKeyboardButton(text="📅 События на день", callback_data="show_day_events"),
        InlineKeyboardButton(text="➕ Новое событие", callback_data="new_event_in_cal")
    ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ На главную", callback_data="back_to_start")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_events_list_keyboard(events: list, date: str = None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора события из списка"""
    keyboard = []

    for idx, event in enumerate(events, 1):
        summary = event.get('summary', 'Без названия')[:40]
        keyboard.append([
            InlineKeyboardButton(
                text=f"{idx}. {summary}",
                callback_data=f"select_event_{event['id']}"
            )
        ])

    # Кнопки действий
    keyboard.append([
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_event_action"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_event_action")
    ])

    if date:
        keyboard.append([
            InlineKeyboardButton(text="📅 Выбрать другую дату", callback_data="choose_other_date")
        ])

    keyboard.append([
        InlineKeyboardButton(text="📋 Все календари", callback_data="back_to_calendars"),
        InlineKeyboardButton(text="⬅️ На главную", callback_data="back_to_start")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_event_edit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для редактирования события"""
    keyboard = [
        [
            InlineKeyboardButton(text="📝 Название", callback_data="edit_field_summary"),
            InlineKeyboardButton(text="📅 Дата/время", callback_data="edit_field_datetime")
        ],
        [
            InlineKeyboardButton(text="📍 Место", callback_data="edit_field_location"),
            InlineKeyboardButton(text="📄 Описание", callback_data="edit_field_description")
        ],
        [
            InlineKeyboardButton(text="👥 Участники", callback_data="edit_field_attendees"),
            InlineKeyboardButton(text="🔄 Повторение", callback_data="edit_field_recurrence")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit"),
            InlineKeyboardButton(text="✅ Готово", callback_data="finish_edit")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_calendar_date_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора даты просмотра событий"""
    today = datetime.now()

    keyboard = [
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data=f"select_date_{today.strftime('%Y-%m-%d')}"),
            InlineKeyboardButton(text="📅 Завтра",
                                 callback_data=f"select_date_{(today + timedelta(days=1)).strftime('%Y-%m-%d')}")
        ],
        [
            InlineKeyboardButton(text="📅 Послезавтра",
                                 callback_data=f"select_date_{(today + timedelta(days=2)).strftime('%Y-%m-%d')}")
        ],
        [
            InlineKeyboardButton(text="📅 Выбрать дату", callback_data="choose_custom_date")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_calendars")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)



def get_confirmation_delete_keyboard(item_type: str = "event") -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления"""
    text_map = {
        "event": "событие",
        "calendar": "календарь"
    }

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"❌ Да, удалить {text_map.get(item_type, '')}",
                callback_data="delete_confirm_yes"
            ),
            InlineKeyboardButton(
                text="✅ Нет, оставить",
                callback_data="delete_confirm_no"
            )
        ]
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_action")]
    ])

def get_calendar_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура действий с календарем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 События на день", callback_data="show_day_events"),
            InlineKeyboardButton(text="➕ Новое событие", callback_data="new_event_in_cal")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить календарь", callback_data="delete_calendar_action"),
            InlineKeyboardButton(text="📋 Все календари", callback_data="back_to_calendars")
        ],
        [
            InlineKeyboardButton(text="⬅️ На главную", callback_data="back_to_start")
        ]
    ])


def get_event_actions_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура действий с событием"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_event_action"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data="delete_event_action")
        ],
        [
            InlineKeyboardButton(text="📅 Назад к событиям", callback_data="back_to_events"),
            InlineKeyboardButton(text="📋 Все календари", callback_data="back_to_calendars")
        ],
        [
            InlineKeyboardButton(text="⬅️ На главную", callback_data="back_to_start")
        ]
    ])


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой пропуска"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_description")]
    ])