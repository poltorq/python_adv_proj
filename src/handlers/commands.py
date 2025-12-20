# from threading import Event

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.lexicon.lexicon_ru import LEXICON_RU
from src.keyboards.keyboards import (
    # get_main_keyboard,
    # get_inline_keyboard,
    get_calendar_keyboard,
    get_time_hour_keyboard,
    get_time_minute_keyboard,
    get_duration_keyboard,
    # get_auth_keyboard,
    get_mode_keyboard,
    get_confirmation_keyboard,
)

router = Router()


# --- FSM ---
class EventStates(StatesGroup):
    choosing_mode = State()
    choosing_date = State()
    choosing_hour = State()
    choosing_minute = State()
    choosing_duration = State()
    confirmation = State()


# --- /start ---
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    user = message.from_user
    if user is None:
        return

    await state.clear()
    await message.answer(
        LEXICON_RU['/start'].format(name=user.first_name),
        reply_markup=get_mode_keyboard(),
    )
    await state.set_state(EventStates.choosing_mode)


# --- /help ---
@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(LEXICON_RU['/help'])


# --- /echo ---
@router.message(Command("echo"))
async def cmd_echo(message: types.Message) -> None:
    if message.text is None:
        await message.answer(LEXICON_RU['echo_empty'])
        return

    text = message.text[6:].strip()
    if not text:
        await message.answer(LEXICON_RU['echo_empty'])
        return

    await message.answer(LEXICON_RU['echo_response'].format(text=text))


# --- /Выбор режима ---
@router.callback_query(F.data.startswith("mode_"), EventStates.choosing_mode)
async def choose_mode(callback: types.CallbackQuery,
                      state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)
    await callback.message.edit_text(
        "Вы выбрали классический режим. Выберите дату события:",
        reply_markup=get_calendar_keyboard()
    )
    await state.set_state(EventStates.choosing_date)
    await callback.answer()


# --- /Переход по месяцам ---
@router.callback_query(F.data.startswith("month_"), EventStates.choosing_date)
async def process_month_switch(callback: types.CallbackQuery) -> None:
    if callback.data is None or callback.message is None:
        return

    _, year_str, month_str = callback.data.split("_")
    year, month = int(year_str), int(month_str)

    await callback.message.edit_text(
        "Выберите дату события:",
        reply_markup=get_calendar_keyboard(year=year, month=month)
    )
    await callback.answer()


# --- Выбор дня ---
@router.callback_query(F.data.startswith("date_"), EventStates.choosing_date)
async def choose_date(callback: types.CallbackQuery,
                      state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, year_str, month_str, day_str = callback.data.split("_")
    year, month, day = int(year_str), int(month_str), int(day_str)

    await state.update_data(date=f"{year}-{month:02d}-{day:02d}")
    await state.set_state(EventStates.choosing_hour)

    await callback.message.edit_text(
        f"Вы выбрали дату: {day}.{month}.{year}\nТеперь выберите час:",
        reply_markup=get_time_hour_keyboard()
    )
    await callback.answer()


# --- /Выбор часа ---
@router.callback_query(F.data.startswith("time_") & ~F.data.contains(":"))
async def choose_hour(callback: types.CallbackQuery,
                      state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    hour = int(callback.data.split("_")[1])
    await state.update_data(hour=hour)
    await state.set_state(EventStates.choosing_minute)

    await callback.message.edit_text(
        f"Вы выбрали час: {hour}. Теперь выберите минуты:",
        reply_markup=get_time_minute_keyboard(hour)
    )
    await callback.answer()


# --- /Выбор минут ---
@router.callback_query(F.data.startswith("time_") & F.data.contains(":"))
async def choose_minute(callback: types.CallbackQuery,
                        state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    _, time_str = callback.data.split("_")
    hour, minute = map(int, time_str.split(":"))

    await state.update_data(minute=minute)
    await state.set_state(EventStates.choosing_duration)

    await callback.message.edit_text(
        f"Вы выбрали время {hour:02d}:{minute:02d}. "
        f"Теперь выберите длительность:",
        reply_markup=get_duration_keyboard()
    )
    await callback.answer()


# --- /Выбор длительности ---
@router.callback_query(F.data.startswith("duration_"))
async def choose_duration(callback: types.CallbackQuery,
                          state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

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


# --- Подтверждение события ---
@router.callback_query(F.data.startswith("confirm_"), EventStates.confirmation)
async def confirm_event(callback: types.CallbackQuery,
                        state: FSMContext) -> None:
    if callback.data is None or callback.message is None:
        return

    if callback.data == "confirm_yes":
        await callback.message.edit_text("✅ Событие сохранено!")
    else:
        await callback.message.edit_text("❌ Событие отменено.")

    await state.clear()
    await callback.answer()


# --- Универсальная кнопка «Назад» ---
@router.callback_query(F.data == "back")
async def go_back(callback: types.CallbackQuery, state: FSMContext) -> None:
    if callback.message is None:
        return

    current_state = await state.get_state()

    if current_state is None:
        await callback.answer("Вы уже на первом шаге", show_alert=True)
        return

    elif current_state.endswith("choosing_date"):
        await state.set_state(None)
        await callback.message.edit_text(
            "Выберите режим события:",
            reply_markup=get_mode_keyboard()
        )

    elif current_state.endswith("choosing_hour"):
        await state.set_state(EventStates.choosing_date)
        await callback.message.edit_text(
            "Выберите дату события:",
            reply_markup=get_calendar_keyboard()
        )

    elif current_state.endswith("choosing_minute"):
        await state.set_state(EventStates.choosing_hour)
        await callback.message.edit_text(
            "Выберите час:",
            reply_markup=get_time_hour_keyboard()
        )

    elif current_state.endswith("choosing_duration"):
        await state.set_state(EventStates.choosing_minute)
        data = await state.get_data()
        await callback.message.edit_text(
            "Выберите минуты:",
            reply_markup=get_time_minute_keyboard(data['hour'])
        )

    elif current_state.endswith("confirmation"):
        await state.set_state(EventStates.choosing_duration)
        data = await state.get_data()
        await callback.message.edit_text(
            "Выберите длительность:",
            reply_markup=get_duration_keyboard()
        )

    await callback.answer()
