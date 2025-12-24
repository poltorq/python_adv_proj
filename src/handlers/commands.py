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
)
from src.service.calendar.client import SimpleGoogleCalendar
from model import process_text, extract_event, format_event_for_display
from src.fallback.fallback_logic import FallbackManager, is_valid_date
import src.clients.deepseek.client as deep_client
import json

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
            "• «Презентация проекта 25 декабря в 14:00 в офисе»"
        )
        await state.set_state(EventStates.waiting_for_text)
    else:
        # Классический режим — переход к выбору даты
        await callback.message.edit_text("Выберите дату события:", reply_markup=get_calendar_keyboard())
        await state.set_state(EventStates.choosing_date)
    
    await callback.answer()


# === AI РЕЖИМ: ОБРАБОТКА ТЕКСТА ===
def validate_event_response(response: dict) -> bool:
    """Проверяет валидность ответа модели."""
    if not response:
        return False
    title = response.get("title")
    date_str = response.get("date")
    return bool(title) and bool(date_str) and is_valid_date(date_str)


def parse_deepseek_response(response_text: str) -> dict:
    """Парсит JSON ответ от DeepSeek."""
    try:
        # Пытаемся найти JSON в ответе
        # DeepSeek может вернуть текст с JSON внутри
        import re
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response_text)
    except (json.JSONDecodeError, AttributeError):
        return {}


@router.message(EventStates.waiting_for_text)
async def process_ai_text(message: types.Message, state: FSMContext):
    user_text = message.text
    if not user_text:
        await message.answer("Пожалуйста, отправьте текстовое описание события.")
        return
    
    await message.answer("🔄 Анализирую текст...")
    
    event_data = None
    used_fallback = False
    
    # === ШАГ 1: Пробуем нашу модель ===
    try:
        event_data = extract_event(user_text)
        print(f"[AI] Ответ модели: {event_data}")
    except Exception as e:
        print(f"[AI] Ошибка модели: {e}")
        event_data = {}
    
    # === ШАГ 2: Проверяем валидность ответа ===
    if not validate_event_response(event_data):
        print("[AI] Ответ модели невалиден, используем DeepSeek fallback...")
        await message.answer("🔄 Уточняю с помощью DeepSeek...")
        
        # === ШАГ 3: Fallback на DeepSeek ===
        try:
            fallback = FallbackManager()
            request = deep_client.ChatRequest(messages=[])
            prompt = deep_client.Message(role="user", content=user_text)
            
            deepseek_response = fallback.run(request, prompt)
            print(f"[AI] Ответ DeepSeek: {deepseek_response}")
            
            # Парсим ответ DeepSeek
            if isinstance(deepseek_response, str):
                parsed = parse_deepseek_response(deepseek_response)
            else:
                parsed = deepseek_response
            
            if parsed:
                # Конвертируем формат DeepSeek в наш формат
                event_data = {
                    "title": parsed.get("title", "Событие"),
                    "date": parsed.get("date"),
                    "time": parsed.get("time"),
                    "datetime": None,
                    "location": parsed.get("loc"),
                    "participants": [parsed.get("user")] if parsed.get("user") else [],
                    "url": parsed.get("url"),
                }
                # Формируем datetime
                if event_data["date"] and event_data["time"]:
                    event_data["datetime"] = f"{event_data['date']}T{event_data['time']}"
                elif event_data["date"]:
                    event_data["datetime"] = f"{event_data['date']}T12:00:00"
                
                used_fallback = True
                
        except Exception as e:
            print(f"[AI] Ошибка DeepSeek fallback: {e}")
    
    # === ШАГ 4: Проверяем итоговый результат ===
    if not event_data or not event_data.get("datetime"):
        await message.answer(
            "❌ Не удалось распознать событие.\n\n"
            "Попробуйте описать событие иначе, например:\n"
            "• «Встреча завтра в 15:00»\n"
            "• «Созвон 25 декабря в 10:30»\n\n"
            "Или используйте классический режим."
        )
        return
    
    # Сохраняем данные в состоянии
    await state.update_data(
        ai_event=event_data,
        original_text=user_text,
        used_fallback=used_fallback
    )
    
    # Формируем сообщение с результатом
    title = event_data.get('title', 'Событие')
    event_datetime = event_data.get('datetime')
    location = event_data.get('location')
    participants = event_data.get('participants', [])
    
    result_text = f"{'🤖' if not used_fallback else '🔮'} Распознано событие"
    if used_fallback:
        result_text += " (DeepSeek)"
    result_text += ":\n\n"
    result_text += f"📝 Название: {title}\n"
    
    if event_datetime:
        try:
            dt = datetime.fromisoformat(event_datetime)
            result_text += f"📅 Дата: {dt.strftime('%d.%m.%Y')}\n"
            result_text += f"🕐 Время: {dt.strftime('%H:%M')}\n"
        except:
            result_text += f"📅 Дата/время: {event_datetime}\n"
    
    if location:
        result_text += f"📍 Место: {location}\n"
    
    if participants and any(participants):
        result_text += f"👥 Участники: {', '.join(filter(None, participants))}\n"
    
    result_text += "\n✅ Создать это событие в календаре?"
    
    await message.answer(result_text, reply_markup=get_confirmation_keyboard())
    await state.set_state(EventStates.ai_confirmation)


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
                "Попробуйте указать дату и время явно."
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
                f"🔗 {event.get('htmlLink', '-')}"
            )
            
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка создания события: {str(e)}")
    else:
        await callback.message.edit_text(
            "❌ Событие отменено.\n\n"
            "Используйте /start чтобы попробовать снова."
        )
    
    await state.clear()
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
            await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
    else:
        await callback.message.edit_text("❌ Событие отменено.")

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
