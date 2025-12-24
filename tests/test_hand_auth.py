import pytest
from unittest.mock import AsyncMock, MagicMock

from aiogram import types

from src.handlers.auth import auth_handler, SERVER_URL


@pytest.mark.asyncio
async def test_auth_handler_sends_auth_message():
    # mock message
    message = MagicMock(spec=types.Message)

    message.from_user = MagicMock()
    message.from_user.id = 12345

    message.chat = MagicMock()
    message.chat.id = 67890

    message.answer = AsyncMock()

    # run handler
    await auth_handler(message)

    # assertions
    message.answer.assert_called_once()

    args, kwargs = message.answer.call_args

    assert "Google Calendar" in args[0]

    reply_markup = kwargs["reply_markup"]
    assert isinstance(reply_markup, types.InlineKeyboardMarkup)

    button = reply_markup.inline_keyboard[0][0]
    assert button.text == "🔐 Авторизоваться через Google"

    expected_url = (
        f"{SERVER_URL}/auth/google?user_id=12345&chat_id=67890"
    )
    assert button.url == expected_url
