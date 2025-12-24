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

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_logic_manual(mock_validate_connection):
    model = MockModel("ok")
    fallback_manager = FallbackManager(model)

    # Scenario 1: Valid custom response, invalid DeepSeek response
    custom_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }
    deepseek_response = {}

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == custom_response

    # Scenario 2: Invalid custom response, valid DeepSeek response
    custom_response = {}
    deepseek_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == deepseek_response

    # Scenario 3: Both responses valid
    custom_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }
    deepseek_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == custom_response

    # Scenario 4: Neither response valid
    custom_response = {}
    deepseek_response = {}

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == deepseek_response

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_valid_custom_response(mock_validate_connection):
    model = MockModel("ok")
    fallback_manager = FallbackManager(model)

    custom_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }
    deepseek_response = {}

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == custom_response

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_valid_deepseek_response(mock_validate_connection):
    model = MockModel("empty")
    fallback_manager = FallbackManager(model)

    custom_response = {}
    deepseek_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == deepseek_response

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_both_responses_valid(mock_validate_connection):
    model = MockModel("ok")
    fallback_manager = FallbackManager(model)

    custom_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }
    deepseek_response = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == custom_response

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_neither_response_valid(mock_validate_connection):
    model = MockModel("empty")
    fallback_manager = FallbackManager(model)

    custom_response = {}
    deepseek_response = {}

    fallback_manager.model.get_answer = lambda prompt: custom_response
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(ChatRequest(messages=[]), Message(role="user", content="Test prompt"))
    assert result == deepseek_response

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_transform_to_ideal_structure(mock_validate_connection):
    model = MockModel("ok")
    fallback_manager = FallbackManager(model)

    user_message = Message(role="user", content="Test prompt")
    chat_request = ChatRequest(messages=[])

    # Mock the DeepSeek response to be empty
    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content={})

    result = fallback_manager.run(chat_request, user_message)

    expected_structure = {
        "title": "встреча",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "офис",
        "user": "Сема",
        "url": "https://zoom.us/..."
    }

    assert result == expected_structure

@patch("src.clients.deepseek.client.DeepSeekClient.validate_connection", return_value=None)
def test_fallback_manager_question_to_deepseek(mock_validate_connection):
    model = MockModel("empty")  # Custom model returns an empty response
    fallback_manager = FallbackManager(model)

    user_message = Message(role="user", content="Какой город столица России?")
    chat_request = ChatRequest(messages=[])

    # Mock the DeepSeek response to return the correct answer
    deepseek_response = {
        "title": "вопрос",
        "date": "2025-04-25",
        "time": "18:00:00",
        "loc": "Москва",
        "user": "Пользователь",
        "url": "https://example.com/answer"
    }

    fallback_manager.deepspeak_model.chat_completion = lambda request: MagicMock(content=deepseek_response)

    result = fallback_manager.run(chat_request, user_message)

    assert result == deepseek_response
