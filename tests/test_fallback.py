import os
import pytest
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from src.fallback.fallback_logic import (
    MockModel,
    is_valid_date,
    is_valid_time,
    FallbackManager
)

from model import extract_event, format_event_for_display, process_text

from src.clients.deepseek.client import ChatRequest, Message, AppConfig
from src.config.config import BotConfig

# Ensure required environment variables are set for tests
os.environ['DeepSeek_api_key'] = os.getenv('DEEPSEEK_API_KEY')
os.environ['BOT_TOKEN'] = 'mock-bot-token'

@dataclass
class DeepSeekConfig:
    api_key: str = os.getenv('DEEPSEEK_API_KEY')

def create_mock_app_config():
    return AppConfig(
        bot=BotConfig(
            token=os.environ['BOT_TOKEN'],
            admins=[],
            use_webhook=False
        ),
        deepseek=DeepSeekConfig(api_key=os.environ['DeepSeek_api_key']),
        debug=True,
        log_level="INFO"
    )

def test_MockModel_mock():
    model = MockModel("ok")
    prompt = "Test prompt"
    system_prompt = "System prompt"

    answer = model.get_answer(prompt, system_prompt)

    assert answer == dict(
                title="встреча",
                date="2025-04-25",
                time="18:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            )
    
    model = MockModel("empty")
    answer = model.get_answer(prompt, system_prompt)
    assert answer == dict()

    model = MockModel("hallucination")
    answer = model.get_answer(prompt, system_prompt)
    assert answer in model.diff_hall

    model = MockModel("shit")
    with pytest.raises(RuntimeError):
        model.get_answer(prompt, system_prompt)

    assert model.generate(prompt, prompt) == "Generated response based on prompt: " + prompt

def test_date_validation_func():
    valid_dates = [
        "2023-10-05",
        "1999-12-31",
        "2000-01-01"
    ]

    invalid_dates = [
        "2023-13-05",  # Invalid month
        "2023-00-10",  # Invalid month
        "2023-02-30",  # Invalid day
        "abcd-ef-gh",  # Non-numeric
        "20231005"    # Wrong format
    ]

    for date in valid_dates:
        assert is_valid_date(date) == True

    for date in invalid_dates:
        assert is_valid_date(date) == False

def test_time_validation_func():
    valid_times = [
        "12:30:45",
        "00:00:00",
        "23:59:59"
    ]

    invalid_times = [
        "24:00:00",  # Invalid hour
        "12:60:30",  # Invalid minute
        "12:30:61",  # Invalid second
        "ab:cd:ef",  # Non-numeric
        "12-30-45"   # Wrong format
    ]

    for time in valid_times:
        assert is_valid_time(time) == True

    for time in invalid_times:
        assert is_valid_time(time) == False

def test_fallback():
    custom_response = extract_event("Встреча 2025-04-25 с Семой в офисе в 18:00 по Zoom. Вот ссылка: https://zoom.us/...")
    assert "title" in custom_response
    assert "date" in custom_response