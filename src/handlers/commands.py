from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncpg
import os

from src.lexicon.lexicon_ru import LEXICON_RU
from src.keyboards.keyboards import (
    get_calendar_keyboard,
    get_time_hour_keyboard,
    get_time_minute_keyboard,
    get_duration_keyboard,
    get_mode_keyboard,
    get_confirmation_keyboard,
    get_add_another_event_keyboard,
    get_ai_back_keyboard,
    get_cancel_keyboard,
    get_calendar_date_keyboard,
    get_calendar_list_keyboard,
    get_event_edit_keyboard,
    get_events_list_keyboard

)
from src.service.calendar.client import SimpleGoogleCalendar
from model import process_text, extract_event, format_event_for_display

router = Router()

import os
import asyncpg
from typing import Dict, Optional

DATABASE_URL = "postgresql://bot_user:bot_password123@213.226.127.133:6432/meeting_bot"


async def get_user_tokens(telegram_id: int) -> Optional[Dict]:
    """ВРОДЕ ЭТО РАБОТАЕТ"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print(f"🔍 Поиск токенов для telegram_id: {telegram_id}")

        user_row = await conn.fetchrow(
            'SELECT id, google_connected FROM users WHERE telegram_id = $1',
            telegram_id
        )

        if not user_row:
            print(f"❌ Пользователь {telegram_id} НЕ НАЙДЕН")
            await conn.close()
            return None

        print(f"✅ Пользователь: ID={user_row['id']}, google_connected={user_row['google_connected']}")

        if not user_row['google_connected']:
            print(f"❌ Google НЕ подключен")
            await conn.close()
            return None

        creds_row = await conn.fetchrow(
            'SELECT access_token, refresh_token FROM google_credentials WHERE user_id = $1',
            user_row['id']
        )

        await conn.close()

        if creds_row:
            print(f"✅ ✅ ТОКЕНЫ НАЙДЕНЫ! {creds_row['access_token'][:30]}...")
            return {
                'access_token': creds_row['access_token'],
                'refresh_token': creds_row['refresh_token'],
                'client_id': os.getenv("GOOGLE_CLIENT_ID"),
                'client_secret': os.getenv("GOOGLE_CLIENT_SECRET")
            }
        else:
            print(f"❌ Нет токенов для user_id {user_row['id']}")
            return None

    except Exception as e:
        print(f"❌ ОШИБКА БД: {e}")
        return None


# === FSM STATES ===
class EventStates(StatesGroup):
    choosing_mode = State()
    choosing_date = State()
    choosing_hour = State()
    choosing_minute = State()
    choosing_duration = State()
    confirmation = State()
    # AI mode states
    waiting_for_text = State()
    ai_confirmation = State()
    # New states for calendar management
    calendar_list = State()
    choose_calendar = State()
    calendar_events_day = State()
    choose_event_for_day = State()
    create_calendar_name = State()
    create_calendar_details = State()
    delete_calendar_confirm = State()
    event_edit_select = State()
    event_edit_field = State()
    event_edit_value = State()
    delete_event_confirm = State()


# === START ===
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    tokens = await get_user_tokens(telegram_id)
    is_authorized = tokens is not None

    await state.clear()
    await state.set_state(EventStates.choosing_mode)

    if not is_authorized:
        SERVER_URL = "http://turbomuza.ru"
        auth_url = f"{SERVER_URL}/auth/google?user_id={telegram_id}&chat_id={message.chat.id}"

        auth_button = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="🔐 Авторизоваться через Google", url=auth_url)]
            ]
        )
        await message.answer("Для работы с Google Calendar нужно авторизоваться:", reply_markup=auth_button)

    await message.answer(
        f"Привет, {user.first_name}! Выберите режим события:",
        reply_markup=get_mode_keyboard()
    )


# ===Auth===
@router.message(Command("auth"))
async def cmd_auth(message: types.Message):
    user = message.from_user
    if not user:
        return

    telegram_id = user.id

    tokens = await get_user_tokens(telegram_id)
    if tokens:
        await message.answer("✅ Google Calendar уже подключён.")
        return

    SERVER_URL = "http://turbomuza.ru"
    auth_url = f"{SERVER_URL}/auth/google?user_id={telegram_id}&chat_id={message.chat.id}"

    auth_button = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🔐 Авторизоваться через Google",
                url=auth_url
            )]
        ]
    )

    await message.answer(
        "🔐 Для работы с Google Calendar требуется авторизация:",
        reply_markup=auth_button
    )



# === ВЫБОР РЕЖИМА ===
@router.message(F.text == "🛠 Выбор режима")
async def choose_mode_text(message: types.Message, state: FSMContext):
    await state.set_state(EventStates.choosing_mode)
    await message.answer("Выберите режим события:", reply_markup=get_mode_keyboard())


@router.callback_query(F.data.startswith("mode_"), EventStates.choosing_mode)
async def choose_mode(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)

    if mode == "ai":
        # AI режим — запрашиваем текст
        await callback.message.edit_text(
            "🤖 AI режим\n\n"
            "Опишите событие текстом, например:\n"
            "• «Встреча с командой завтра в 15:00 в Zoom»\n"
            "• «Созвон с Петей в понедельник в 10:30»\n"
            "• «Презентация проекта 25 декабря в 14:00 в офисе»",
            reply_markup=get_ai_back_keyboard()
        )
        await state.set_state(EventStates.waiting_for_text)
    else:
        # Классический режим — переход к выбору даты
        await callback.message.edit_text("Выберите дату события:", reply_markup=get_calendar_keyboard())
        await state.set_state(EventStates.choosing_date)

    await callback.answer()


# === AI РЕЖИМ: ОБРАБОТКА ТЕКСТА ===
@router.message(EventStates.waiting_for_text)
async def process_ai_text(message: types.Message, state: FSMContext):
    user_text = message.text
    if not user_text:
        await message.answer("Пожалуйста, отправьте текстовое описание события.")
        return

    await message.answer("🔄 Анализирую текст...")

    try:
        # Вызываем модель для извлечения события
        event_data = extract_event(user_text)

        # Сохраняем данные в состоянии
        await state.update_data(
            ai_event=event_data,
            original_text=user_text
        )

        # Формируем сообщение с результатом
        title = event_data.get('title', 'Событие')
        event_datetime = event_data.get('datetime')
        location = event_data.get('location')
        participants = event_data.get('participants', [])

        result_text = f"🤖 Распознано событие:\n\n"
        result_text += f"📝 Название: {title}\n"

        if event_datetime:
            # Парсим datetime и форматируем красиво
            try:
                dt = datetime.fromisoformat(event_datetime)
                result_text += f"📅 Дата: {dt.strftime('%d.%m.%Y')}\n"
                result_text += f"🕐 Время: {dt.strftime('%H:%M')}\n"
            except:
                result_text += f"📅 Дата/время: {event_datetime}\n"

        if location:
            result_text += f"📍 Место: {location}\n"

        if participants:
            result_text += f"👥 Участники: {', '.join(participants)}\n"

        result_text += "\n✅ Создать это событие в календаре?"

        await message.answer(result_text, reply_markup=get_confirmation_keyboard())
        await state.set_state(EventStates.ai_confirmation)

    except Exception as e:
        await message.answer(
            f"❌ Не удалось распознать событие: {str(e)}\n\n"
            "Попробуйте описать событие иначе или используйте классический режим.",
            reply_markup=get_add_another_event_keyboard()
        )


# === AI РЕЖИМ: ПОДТВЕРЖДЕНИЕ ===
@router.callback_query(F.data.startswith("confirm_"), EventStates.ai_confirmation)
async def confirm_ai_event(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = callback.from_user.id

    if callback.data == "confirm_yes":
        tokens = await get_user_tokens(telegram_id)

        if not tokens:
            await callback.message.edit_text("❌ Авторизуйтесь через Google: /start")
            await state.clear()
            return

        event_data = data.get('ai_event', {})

        # Получаем данные события
        title = event_data.get('title', 'Новое событие')
        event_datetime = event_data.get('datetime')
        location = event_data.get('location')

        if not event_datetime:
            await callback.message.edit_text(
                "❌ Не удалось определить дату/время события.\n"
                "Попробуйте указать дату и время явно.",
                reply_markup=get_add_another_event_keyboard()
            )
            await state.clear()
            return

        try:
            # Парсим datetime
            dt_start = datetime.fromisoformat(event_datetime)
            dt_end = dt_start + timedelta(hours=1)  # По умолчанию 1 час

            start_time = dt_start.strftime("%Y-%m-%dT%H:%M:%S")
            end_time = dt_end.strftime("%Y-%m-%dT%H:%M:%S")

            gcal = SimpleGoogleCalendar(
                client_id=tokens['client_id'],
                client_secret=tokens['client_secret']
            )

            event = gcal.create_event(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                calendar_id="primary",
                title=title,
                start_time=start_time,
                end_time=end_time,
                timezone="Europe/Moscow",
                location=location
            )

            await callback.message.edit_text(
                f"✅ Событие создано!\n\n"
                f"📝 {event.get('summary', title)}\n"
                f"📅 {dt_start.strftime('%d.%m.%Y %H:%M')}\n"
                f"🔗 {event.get('html_link', '-')}"
            )

        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка создания события: {str(e)}")
    else:
        await callback.message.edit_text(
            "❌ Событие отменено.\n\n"
            "Используйте /start чтобы попробовать снова.",
            reply_markup=get_add_another_event_keyboard()
        )

    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "ai_back", EventStates.waiting_for_text)
async def ai_back_to_mode(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EventStates.choosing_mode)

    await callback.message.edit_text(
        "Выберите режим события:",
        reply_markup=get_mode_keyboard()
    )

    await callback.answer()



# === ВЫБОР ДАТЫ ===
@router.callback_query(F.data.startswith("month_"), EventStates.choosing_date)
async def switch_month(callback: types.CallbackQuery):
    _, year_str, month_str = callback.data.split("_")
    year, month = int(year_str), int(month_str)
    await callback.message.edit_text(
        "Выберите дату события:",
        reply_markup=get_calendar_keyboard(year=year, month=month)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("date_"), EventStates.choosing_date)
async def choose_date(callback: types.CallbackQuery, state: FSMContext):
    _, year_str, month_str, day_str = callback.data.split("_")
    year, month, day = int(year_str), int(month_str), int(day_str)
    await state.update_data(date=f"{year}-{month:02d}-{day:02d}")
    await state.set_state(EventStates.choosing_hour)
    await callback.message.edit_text(
        f"Вы выбрали дату: {day}.{month}.{year}\nТеперь выберите час:",
        reply_markup=get_time_hour_keyboard()
    )
    await callback.answer()


# === ВЫБОР ВРЕМЕНИ ===
@router.callback_query(F.data.startswith("time_") & ~F.data.contains(":"), EventStates.choosing_hour)
async def choose_hour(callback: types.CallbackQuery, state: FSMContext):
    hour = int(callback.data.split("_")[1])
    await state.update_data(hour=hour)
    await state.set_state(EventStates.choosing_minute)
    await callback.message.edit_text(
        f"Вы выбрали час: {hour}. Теперь выберите минуты:",
        reply_markup=get_time_minute_keyboard(hour)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("time_") & F.data.contains(":"), EventStates.choosing_minute)
async def choose_minute(callback: types.CallbackQuery, state: FSMContext):
    _, time_str = callback.data.split("_")
    hour, minute = map(int, time_str.split(":"))
    await state.update_data(minute=minute)
    await state.set_state(EventStates.choosing_duration)
    await callback.message.edit_text(
        f"Вы выбрали время {hour:02d}:{minute:02d}. Теперь выберите длительность:",
        reply_markup=get_duration_keyboard()
    )
    await callback.answer()


# === ВЫБОР ДЛИТЕЛЬНОСТИ ===
@router.callback_query(F.data.startswith("duration_"), EventStates.choosing_duration)
async def choose_duration(callback: types.CallbackQuery, state: FSMContext):
    duration = int(callback.data.split("_")[1])
    await state.update_data(duration=duration)
    await state.set_state(EventStates.confirmation)

    data = await state.get_data()
    await callback.message.edit_text(
        f"✅ Подтверждение события:\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['hour']:02d}:{data['minute']:02d}\n"
        f"Длительность: {data['duration']} мин",
        reply_markup=get_confirmation_keyboard()
    )
    await callback.answer()


# === ПОДТВЕРЖДЕНИЕ ===
@router.callback_query(F.data.startswith("confirm_"), EventStates.confirmation)
async def confirm_event(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = callback.from_user.id

    # ✅ ТОКЕНЫ ИЗ БД через JOIN!
    tokens = await get_user_tokens(telegram_id)

    if callback.data == "confirm_yes":
        if not tokens:
            await callback.message.edit_text("❌ Авторизуйтесь: /auth")
            return

        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        start_time = f"{data['date']}T{data['hour']:02d}:{data['minute']:02d}:00"
        end_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S") + timedelta(minutes=data['duration'])
        end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            event = gcal.create_event(
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                calendar_id="primary",
                title="Новое событие",
                start_time=start_time,
                end_time=end_time,
                timezone="Europe/Moscow"
            )
            await callback.message.edit_text(
                f"✅ Событие сохранено!\n"
                f"Название: {event['summary']}\n"
                f"Ссылка: {event.get('html_link', '-')}"
            )
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {str(e)}",
                                             reply_markup=get_add_another_event_keyboard())
    else:
        await callback.message.edit_text("❌ Событие отменено.",
                                         reply_markup=get_add_another_event_keyboard())


    await state.clear()
    await callback.answer()


# === КНОПКА НАЗАД ===
@router.callback_query(F.data == "back")
async def go_back(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()

    if current_state == EventStates.choosing_date.state:
        await state.set_state(EventStates.choosing_mode)
        await callback.message.edit_text("Выберите режим события:", reply_markup=get_mode_keyboard())
    elif current_state == EventStates.choosing_hour.state:
        await state.set_state(EventStates.choosing_date)
        await callback.message.edit_text("Выберите дату события:", reply_markup=get_calendar_keyboard())
    elif current_state == EventStates.choosing_minute.state:
        await state.set_state(EventStates.choosing_hour)
        await callback.message.edit_text("Выберите час:", reply_markup=get_time_hour_keyboard())
    elif current_state == EventStates.choosing_duration.state:
        await state.set_state(EventStates.choosing_minute)
        hour = data.get('hour', 0)
        await callback.message.edit_text("Выберите минуты:", reply_markup=get_time_minute_keyboard(hour))
    elif current_state == EventStates.confirmation.state:
        await state.set_state(EventStates.choosing_duration)
        await callback.message.edit_text("Выберите длительность:", reply_markup=get_duration_keyboard())
    elif current_state == EventStates.ai_confirmation.state:
        # Возврат к вводу текста в AI режиме
        await state.set_state(EventStates.choosing_mode)
        await callback.message.edit_text("Выберите режим события:", reply_markup=get_mode_keyboard())



    await callback.answer()

# === Going back to the begining ===
@router.callback_query(F.data == "add_another_event")
async def add_another_event(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EventStates.choosing_mode)

    await callback.message.edit_text(
        "Выберите режим события:",
        reply_markup=get_mode_keyboard()
    )

    await callback.answer()

@router.message(Command("echo"))
async def cmd_echo(message: types.Message) -> None:
    await message.answer("Некорректный ввод")

# === HELP COMMAND ===
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Показать справку по командам"""
    help_text = """
            📋 *Доступные команды:*
            
            *Основные:*
            /start - Начать работу с ботом
            /auth - Подключить Google Calendar
            /help - Эта справка
            
            *Работа с календарями:*
            /calendars - Показать все мои календари
            /new_calendar - Создать новый календарь
            
            *Работа с событиями:*
            /events - Показать события на сегодня
            /create_event - Создать событие вручную
            /ai_event - Создать событие с помощью AI
            
            *Управление событиями:*
            /edit_event - Редактировать существующее событие
            /delete_event - Удалить событие
            /delete_calendar - Удалить календарь
            
            *Как использовать:*
            1️⃣ Сначала авторизуйтесь через /auth
            2️⃣ Посмотрите свои календари через /calendars
            3️⃣ Создавайте события через /create_event или /ai_event
            4️⃣ Управляйте событиями через /edit_event или /delete_event
            
            💡 *Совет:* Также можно просто нажать /start для начала работы с меню!
            """
    await message.answer(help_text, parse_mode="Markdown")


# === NEW CALENDAR COMMAND ===
@router.message(Command("new_calendar"))
async def cmd_new_calendar(message: types.Message, state: FSMContext):
    """Создать новый календарь"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    await message.answer(
        "📝 Введите название нового календаря:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(EventStates.create_calendar_name)


# === CALENDARS COMMAND ===
@router.message(Command("calendars"))
async def cmd_calendars(message: types.Message, state: FSMContext):
    """Показать список всех календарей"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        calendars = gcal.list_calendars(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token']
        )

        if not calendars:
            await message.answer("📭 У вас нет календарей.")
            return

        text = "📅 *Ваши календари:*\n\n"
        for idx, cal in enumerate(calendars, 1):
            primary = "⭐ " if cal.get('primary') else ""
            text += f"*{idx}. {primary}{cal.get('summary')}*\n"
            if cal.get('description'):
                text += f"   Описание: {cal.get('description')[:50]}...\n"
            if cal.get('time_zone'):
                text += f"   Часовой пояс: {cal.get('time_zone')}\n"
            text += "\n"

        text += "💡 *Выберите календарь для работы с ним*"

        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_calendar_list_keyboard(calendars)
        )
        await state.set_state(EventStates.calendar_list)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


# === EVENTS COMMAND ===
@router.message(Command("events"))
async def cmd_events(message: types.Message, state: FSMContext):
    """Показать события на сегодня"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        # Используем primary календарь по умолчанию
        events = gcal.list_events_for_day(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            date=datetime.now().strftime('%Y-%m-%d'),
            timezone="Europe/Moscow"
        )

        if not events:
            await message.answer("📭 На сегодня событий нет.")
            return

        text = f"📅 *События на сегодня:*\n\n"
        for idx, event in enumerate(events, 1):
            start_time = event.get('start')
            summary = event.get('summary', 'Без названия')

            # Парсим время
            try:
                if 'T' in start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                else:
                    time_str = "Весь день"
            except:
                time_str = start_time

            text += f"*{idx}. ⏰ {time_str} - {summary}*\n"
            if event.get('location'):
                text += f"   📍 {event.get('location')}\n"
            text += "\n"

        text += "💡 *Выберите событие для действий*"

        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_events_list_keyboard(events)
        )
        await state.set_state(EventStates.choose_event_for_day)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")


# === CREATE EVENT COMMAND ===
@router.message(Command("create_event"))
async def cmd_create_event(message: types.Message, state: FSMContext):
    """Создать событие вручную"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    await state.clear()
    await state.set_state(EventStates.choosing_mode)

    await message.answer(
        "📝 *Создание события*\n\nВыберите режим события:",
        parse_mode="Markdown",
        reply_markup=get_mode_keyboard()
    )


# === AI EVENT COMMAND ===
@router.message(Command("ai_event"))
async def cmd_ai_event(message: types.Message, state: FSMContext):
    """Создать событие с помощью AI"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    await state.clear()
    await state.set_state(EventStates.waiting_for_text)

    await message.answer(
        "🤖 *AI режим создания события*\n\n"
        "Опишите событие текстом, например:\n"
        "• «Встреча с командой завтра в 15:00 в Zoom»\n"
        "• «Созвон с Петей в понедельник в 10:30»\n"
        "• «Презентация проекта 25 декабря в 14:00 в офисе»\n"
        "• «Обед с клиентом сегодня в 13:00 в ресторане»",
        parse_mode="Markdown",
        reply_markup=get_ai_back_keyboard()
    )


# === EDIT EVENT COMMAND ===
@router.message(Command("edit_event"))
async def cmd_edit_event(message: types.Message, state: FSMContext):
    """Редактировать событие"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    await message.answer(
        "✏️ *Редактирование события*\n\n"
        "Чтобы отредактировать событие:\n"
        "1. Сначала посмотрите события через /events\n"
        "2. Выберите событие для редактирования\n"
        "3. Нажмите кнопку '✏️ Редактировать'",
        parse_mode="Markdown"
    )


#
# === ВОЗВРАТ К СПИСКУ СОБЫТИЙ ===
@router.callback_query(F.data == "back_to_event_list")
async def back_to_event_list(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку событий"""
    # Получаем данные из состояния
    data = await state.get_data()
    date_str = data.get('delete_date', '')
    display_date = data.get('display_date', '')
    events = data.get('delete_events', [])

    if not events:
        await callback.answer("Нет событий")
        return

    # Повторно показываем список событий
    text = f"🗑 *События на {display_date}:*\n\n"

    for idx, event in enumerate(events, 1):
        start_time = event.get('start', '')
        summary = event.get('summary', 'Без названия')

        try:
            if 'T' in start_time:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            else:
                time_str = "Весь день"
        except:
            time_str = start_time

        text += f"*{idx}. ⏰ {time_str} - {summary}*\n"
        if event.get('location'):
            text += f"   📍 {event.get('location')}\n"
        text += "\n"

    text += "*Выберите событие для удаления:*"

    # Создаем клавиатуру
    keyboard_buttons = []

    for idx, event in enumerate(events, 1):
        summary_short = event.get('summary', 'Без названия')[:30]
        event_id = event.get('id', '')

        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text=f"{idx}. {summary_short}",
                callback_data=f"choose_event_{event_id}"
            )
        ])

    keyboard_buttons.append([
        types.InlineKeyboardButton(
            text="📅 Другая дата",
            callback_data="cmd_delete_event"
        ),
        types.InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_delete"
        )
    ])

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    await callback.answer()


# === UNKNOWN COMMAND HANDLER ===
@router.message(F.text.startswith("/"))
async def unknown_command(message: types.Message):
    known_commands = [
        "/start", "/auth", "/help",
        "/calendars", "/events", "/new_calendar",
        "/create_event", "/ai_event", "/edit_event",
        "/delete_event", "/delete_calendar"
    ]

    command = message.text.split()[0]
    if command not in known_commands:
        await message.answer(
            "❓ *Неизвестная команда*\n\n"
            "📋 *Доступные команды:*\n"
            "/start — начать работу с ботом\n"
            "/auth — подключить Google Calendar\n"
            "/help — показать справку\n\n"
            "/calendars — список моих календарей\n"
            "/events — события на сегодня\n"
            "/new_calendar — создать новый календарь\n\n"
            "/create_event — создать событие вручную\n"
            "/ai_event — создать событие через AI\n\n"
            "/edit_event — редактировать событие\n"
            "/delete_event — удалить событие\n"
            "/delete_calendar — удалить календарь\n\n"
            "💡 *Или просто нажмите /start для начала работы*",
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "back_to_events")
async def back_to_events(callback: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку событий"""
    data = await state.get_data()
    date_str = data.get('current_date', datetime.now().strftime('%Y-%m-%d'))
    calendar_id = data.get('selected_calendar_id', 'primary')

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        events = gcal.list_events_for_day(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            calendar_id=calendar_id,
            date=date_str,
            timezone="Europe/Moscow"
        )

        if not events:
            await callback.message.answer(f"📭 На {date_str} событий нет.")
            return

        # Сохраняем события для дальнейших действий
        await state.update_data(current_events=events)

        text = f"📅 События на {date_str}:\n\n"
        for idx, event in enumerate(events, 1):
            summary = event.get('summary', 'Без названия')
            start_time = event.get('start', '')

            # Форматируем время
            try:
                if 'T' in start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                else:
                    time_str = "Весь день"
            except:
                time_str = start_time

            text += f"{idx}. ⏰ {time_str} - {summary}\n"
            if event.get('location'):
                text += f"   📍 {event.get('location')}\n"
            text += "\n"

        await callback.message.answer(
            text,
            reply_markup=get_events_list_keyboard(events, date_str)
        )
        await state.set_state(EventStates.choose_event_for_day)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


# ==================== УДАЛЕНИЕ СОБЫТИЙ ЧЕРЕЗ КАЛЕНДАРЬ ====================

# === КОМАНДА ДЛЯ УДАЛЕНИЯ СОБЫТИЯ ===
@router.message(Command("delete_event"))
async def cmd_delete_event(message: types.Message, state: FSMContext):
    """Начало процесса удаления события - показываем календарь"""
    telegram_id = message.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    await message.answer(
        "🗑 *Удаление события*\n\n"
        "Выберите дату, на которой хотите удалить событие:",
        parse_mode="Markdown",
        reply_markup=get_calendar_date_keyboard()
    )

    # Сохраняем action для понимания, что это удаление
    await state.update_data(action="delete")
    await state.set_state(EventStates.calendar_events_day)


# === ОБРАБОТЧИК ДЛЯ ВЫБОРА ДАТЫ ИЗ КАЛЕНДАРЯ (УДАЛЕНИЕ) ===
@router.callback_query(F.data.startswith("select_date_"), EventStates.calendar_events_day)
async def select_date_for_delete_flow(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал дату - показываем события для удаления"""
    date_str = callback.data.replace("select_date_", "")

    print(f"🔔 Выбрана дата для удаления: {date_str}")

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await callback.message.answer("❌ Авторизуйтесь через Google: /auth")
        await callback.answer()
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        # Получаем события на выбранную дату
        events = gcal.list_events_for_day(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            date=date_str,
            timezone="UTC"  # Используем UTC
        )

        print(f"📊 На дату {date_str} найдено событий: {len(events) if events else 0}")

        if not events:
            await callback.message.answer(f"📭 На {date_str} событий нет для удаления.")
            await callback.answer()
            return

        # Сохраняем события в состоянии
        await state.update_data(
            current_events=events,
            current_date=date_str,
            action="delete"
        )

        # Формируем сообщение со списком событий
        text = f"🗑 *События на {date_str}:*\n\n"

        for idx, event in enumerate(events, 1):
            start_time = event.get('start')
            summary = event.get('summary', 'Без названия')

            # Форматируем время для отображения
            try:
                if 'T' in start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                else:
                    time_str = "Весь день"
            except:
                time_str = start_time

            text += f"*{idx}. ⏰ {time_str} - {summary}*\n"
            if event.get('location'):
                text += f"   📍 {event.get('location')}\n"
            text += "\n"

        text += "*Выберите событие для удаления:*"

        # Создаем клавиатуру с событиями в виде кнопок
        keyboard_buttons = []

        for idx, event in enumerate(events, 1):
            summary_short = event.get('summary', 'Без названия')[:30]
            event_id = event.get('id', '')

            keyboard_buttons.append([
                types.InlineKeyboardButton(
                    text=f"{idx}. {summary_short}",
                    callback_data=f"direct_delete_{event_id}"
                )
            ])

        # Добавляем кнопки навигации
        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="📅 Выбрать другую дату",
                callback_data="choose_other_date_for_delete"
            )
        ])

        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="⬅️ В меню",
                callback_data="back_to_start"
            )
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await state.set_state(EventStates.choose_event_for_day)

    except Exception as e:
        print(f"💥 Ошибка при загрузке событий: {str(e)}")
        await callback.message.answer(f"❌ Ошибка: {str(e)}")

    await callback.answer()


# === КНОПКА "ВЫБРАТЬ ДРУГУЮ ДАТУ" ДЛЯ УДАЛЕНИЯ ===
@router.callback_query(F.data == "choose_other_date_for_delete")
async def choose_other_date_for_delete(callback: types.CallbackQuery, state: FSMContext):
    """Показать календарь для выбора другой даты (удаление)"""
    await callback.message.answer(
        "📅 Выберите другую дату для удаления событий:",
        reply_markup=get_calendar_date_keyboard()
    )
    await state.update_data(action="delete")
    await state.set_state(EventStates.calendar_events_day)
    await callback.answer()


# === ПРЯМОЕ УДАЛЕНИЕ СОБЫТИЯ (БЕЗ ПОДТВЕРЖДЕНИЯ) ===
@router.callback_query(F.data.startswith("direct_delete_"))
async def direct_delete_event(callback: types.CallbackQuery, state: FSMContext):
    """Прямое удаление события при нажатии на кнопку"""
    event_id = callback.data.replace("direct_delete_", "")

    print(f"🔔 Прямое удаление события: ID={event_id}")

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await callback.message.answer("❌ Авторизуйтесь через Google: /auth")
        await callback.answer()
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        # Получаем информацию о событии для отображения
        data = await state.get_data()
        events = data.get('current_events', [])

        event_to_delete = None
        for event in events:
            if event.get('id') == event_id:
                event_to_delete = event
                break

        event_title = event_to_delete.get('summary', 'Событие') if event_to_delete else "Событие"

        # Показываем уведомление об удалении
        delete_message = await callback.message.answer(
            f"🔄 *Удаляю событие...*\n\n"
            f"📝 {event_title}",
            parse_mode="Markdown"
        )

        # Вызываем метод delete_event
        success = gcal.delete_event(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            calendar_id="primary",  # Используем основной календарь
            event_id=event_id
        )

        # Удаляем сообщение об удалении
        try:
            await delete_message.delete()
        except:
            pass

        if success:
            await callback.message.answer(
                f"✅ *Событие успешно удалено!*\n\n"
                f"📝 *Название:* {event_title}\n\n"
                f"Что дальше?\n"
                f"• Удалить еще одно событие — нажмите /delete_event\n"
                f"• Вернуться в меню — нажмите /start",
                parse_mode="Markdown",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🗑 Удалить еще",
                            callback_data="cmd_delete_event"
                        ),
                        types.InlineKeyboardButton(
                            text="🏠 В меню",
                            callback_data="back_to_start"
                        )
                    ]
                ])
            )
        else:
            await callback.message.answer("❌ Не удалось удалить событие.")

    except Exception as e:
        print(f"💥 Ошибка при удалении: {str(e)}")
        await callback.message.answer("Событие удалено!"
        )

    await state.clear()
    await callback.answer()


# === ОБРАБОТЧИК ДЛЯ КНОПКИ "ВЫВЕСТИ СПИСОК СОБЫТИЙ" ===
@router.callback_query(F.data == "cmd_delete_event")
async def handle_delete_event_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Удалить событие'"""

    await callback.answer("🗑 Загружаю календарь...")

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await callback.message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    # Просто показываем календарь
    await callback.message.answer(
        "🗑 Удаление события\n\n"
        "Выберите дату:",
        reply_markup=get_calendar_date_keyboard()
    )

    # Не нужно action="delete"
    await state.set_state(EventStates.calendar_events_day)


@router.callback_query(F.data.startswith("select_date_"), EventStates.calendar_events_day)
async def select_date_for_delete(callback: types.CallbackQuery, state: FSMContext):
    """Пользователь выбрал дату - показываем события"""

    date_str = callback.data.replace("select_date_", "")
    await callback.answer(f"📅 Загружаю события на {date_str}...")

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await callback.message.answer("❌ Авторизуйтесь через Google: /auth")
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        # Получаем события
        events = gcal.list_events_for_day(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            date=date_str,
            timezone="UTC"
        )

        if not events:
            await callback.message.answer(f"📭 На {date_str} событий нет.")
            return

        # Сохраняем только для отображения
        await state.update_data(
            current_events=events,
            current_date=date_str
        )

        # Формируем сообщение
        text = f"🗑 События на {date_str}:\n\n"

        for idx, event in enumerate(events, 1):
            start_time = event.get('start', '')
            summary = event.get('summary', 'Без названия')

            try:
                if 'T' in start_time:
                    dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M')
                else:
                    time_str = "Весь день"
            except:
                time_str = start_time

            text += f"{idx}. ⏰ {time_str} - {summary}\n"
            if event.get('location'):
                text += f"   📍 {event.get('location')}\n"
            text += "\n"

        text += "Нажмите на событие, чтобы удалить его:"

        # Создаем кнопки
        keyboard_buttons = []

        for idx, event in enumerate(events, 1):
            summary_short = event.get('summary', 'Без названия')[:30]
            event_id = event.get('id', '')

            keyboard_buttons.append([
                types.InlineKeyboardButton(
                    text=f"{idx}. {summary_short}",
                    callback_data=f"delete_now_{event_id}"
                )
            ])

        keyboard_buttons.append([
            types.InlineKeyboardButton(
                text="📅 Другая дата",
                callback_data="cmd_delete_event"
            ),
            types.InlineKeyboardButton(
                text="🏠 В меню",
                callback_data="back_to_start"
            )
        ])

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.answer(text, reply_markup=keyboard)

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка: {str(e)}")


@router.callback_query(F.data.startswith("delete_now_"))
async def delete_now_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для немедленного удаления события"""
    event_id = callback.data.replace("delete_now_", "")

    print(f"🔔 Удаление события через delete_now_: ID={event_id}")

    telegram_id = callback.from_user.id
    tokens = await get_user_tokens(telegram_id)

    if not tokens:
        await callback.message.answer("❌ Авторизуйтесь через Google: /auth")
        await callback.answer()
        return

    try:
        gcal = SimpleGoogleCalendar(
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret']
        )

        # Получаем информацию о событии
        data = await state.get_data()
        events = data.get('current_events', [])

        event_to_delete = None
        event_title = "Событие"
        for event in events:
            if event.get('id') == event_id:
                event_to_delete = event
                event_title = event.get('summary', 'Событие')
                break

        # Показываем уведомление об удалении
        delete_message = await callback.message.answer(f"🔄 Удаляю событие: {event_title}...")

        # Вызываем метод delete_event
        success = gcal.delete_event(
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            calendar_id="primary",
            event_id=event_id
        )

        # Удаляем сообщение об удалении
        try:
            await delete_message.delete()
        except:
            pass

        if success:
            await callback.message.answer(
                f"✅ Событие успешно удалено!\n\n"
                f"📝 Название: {event_title}\n\n"
                f"Что дальше?\n"
                f"• Удалить еще одно событие — нажмите /delete_event\n"
                f"• Вернуться в меню — нажмите /start",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="🗑 Удалить еще",
                            callback_data="cmd_delete_event"
                        ),
                        types.InlineKeyboardButton(
                            text="🏠 В меню",
                            callback_data="back_to_start"
                        )
                    ]
                ])
            )
        else:
            await callback.message.answer("❌ Не удалось удалить событие.")

    except Exception as e:
        await callback.message.answer("Событие удалено!")

    await state.clear()
    await callback.answer()
# === Unpredicatble command ===
@router.message(F.text.startswith("/"))
async def unknown_command(message: types.Message):
    known_commands = [
        "/start", "/auth", "/help",
        "/calendars", "/events", "/new_calendar"
    ]

    if message.text.split()[0] not in known_commands:
        await message.answer(
            "❓ Неизвестная команда.\n\n"
            "Доступные команды:\n"
            "/start — начать работу\n"
            "/auth — подключить Google Calendar\n"
            "/help — справка\n"
            "/calendars — список календарей\n"
            "/events — события на сегодня\n"
            "/new_calendar — создать календарь"
        )