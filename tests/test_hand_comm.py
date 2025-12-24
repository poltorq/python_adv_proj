import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import types

from src.handlers.commands import (
    cmd_start,
    cmd_help,
    cmd_echo,
    choose_mode,
    process_month_switch,
    choose_date,
    choose_hour,
    choose_minute,
    choose_duration,
    confirm_event,
    go_back,
    EventStates,
)


@pytest.mark.asyncio
async def test_cmd_start_sets_state_and_sends_message():
    message = MagicMock(spec=types.Message)
    state = AsyncMock()

    message.from_user = MagicMock()
    message.from_user.first_name = "Nikita"
    message.answer = AsyncMock()

    await cmd_start(message, state)

    message.answer.assert_called_once()
    args, kwargs = message.answer.call_args

    assert "Nikita" in args[0]
    assert "reply_markup" in kwargs

    state.clear.assert_awaited_once()
    state.set_state.assert_awaited_once_with(EventStates.choosing_mode)


@pytest.mark.asyncio
async def test_cmd_help_sends_help_message():
    message = MagicMock(spec=types.Message)
    message.answer = AsyncMock()

    await cmd_help(message)

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_cmd_echo_with_empty_text():
    message = MagicMock(spec=types.Message)
    message.text = None
    message.answer = AsyncMock()

    await cmd_echo(message)

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_choose_mode_updates_state_and_edits_message():
    callback = MagicMock(spec=types.CallbackQuery)
    state = AsyncMock()

    callback.data = "mode_ai"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await choose_mode(callback, state)

    state.update_data.assert_awaited_once_with(mode="ai")
    state.set_state.assert_awaited_once_with(EventStates.choosing_date)
    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_month_switch_edits_message():
    callback = MagicMock(spec=types.CallbackQuery)
    callback.data = "month_2025_12"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await process_month_switch(callback)

    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_choose_date_updates_state_and_edits_message():
    callback = MagicMock(spec=types.CallbackQuery)
    state = AsyncMock()

    callback.data = "date_2025_12_24"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await choose_date(callback, state)

    state.update_data.assert_awaited_once_with(date="2025-12-24")
    state.set_state.assert_awaited_once_with(EventStates.choosing_hour)
    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_choose_hour_updates_state_and_edits_message():
    callback = MagicMock(spec=types.CallbackQuery)
    state = AsyncMock()

    callback.data = "time_15"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await choose_hour(callback, state)

    state.update_data.assert_awaited_once_with(hour=15)
    state.set_state.assert_awaited_once_with(EventStates.choosing_minute)
    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_choose_minute_updates_state_and_edits_message():
    callback = MagicMock(spec=types.CallbackQuery)
    state = AsyncMock()

    callback.data = "time_15:30"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await choose_minute(callback, state)

    state.update_data.assert_awaited_once_with(minute=30)
    state.set_state.assert_awaited_once_with(EventStates.choosing_duration)
    callback.message.edit_text.assert_awaited_once()
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_event_saves_or_cancels_event():
    callback = MagicMock(spec=types.CallbackQuery)
    state = AsyncMock()

    callback.data = "confirm_yes"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()

    await confirm_event(callback, state)

    callback.message.edit_text.assert_awaited_once_with("✅ Событие сохранено!")
    state.clear.assert_awaited()
    callback.answer.assert_awaited_once()

    callback.data = "confirm_no"
    callback.message.edit_text.reset_mock()
    state.clear.reset_mock()

    await confirm_event(callback, state)

    callback.message.edit_text.assert_awaited_once_with("❌ Событие отменено.")
    state.clear.assert_awaited()
    callback.answer.assert_awaited()
