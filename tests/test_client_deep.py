# tests/test_deepseek_client.py
import pytest
from unittest.mock import patch, MagicMock
from src.clients.deepseek.client import DeepSeekClient, ChatRequest, Message, ChatResponse, Usage
from src.config.config import AppConfig

# фикстура с конфигом
@pytest.fixture
def mock_config():
    class DeepSeekConfig:
        api_key = "fake_api_key"
        base_url = "https://fake-deepseek.com"
        model = "deepseek-model"
    class Config:
        deepseek = DeepSeekConfig()
    return Config()

# мок ответа OpenAI
@pytest.fixture
def mock_openai_response():
    mock_response = MagicMock()
    mock_response.model = "deepseek-model"
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello from DeepSeek!"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 10
    mock_response.usage.total_tokens = 15
    return mock_response

# ===================== TEST INIT =====================
@patch("src.clients.deepseek.client.OpenAI")
def test_init_creates_client(mock_openai, mock_config):
    mock_openai.return_value.chat.completions.create.return_value = MagicMock()
    client = DeepSeekClient(mock_config)
    assert client.api_key == "fake_api_key"
    assert client.model == "deepseek-model"
    mock_openai.assert_called_once_with(
        api_key="fake_api_key",
        base_url="https://fake-deepseek.com",
        timeout=30,
        max_retries=3
    )
    # validate_connection вызывается внутри конструктора
    mock_openai.return_value.chat.completions.create.assert_called_with(
        model="deepseek-model",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1
    )

# ===================== TEST CHAT COMPLETION =====================
@patch("src.clients.deepseek.client.OpenAI")
def test_chat_completion_returns_response(mock_openai, mock_config, mock_openai_response):
    # Мок OpenAI
    mock_openai.return_value = MagicMock()
    mock_openai.return_value.chat.completions.create.return_value = mock_openai_response

    client = DeepSeekClient(mock_config)
    request = ChatRequest(messages=[Message(role="user", content="Hello")])
    response: ChatResponse = client.chat_completion(request)

    # Проверяем тип и значения
    assert isinstance(response, ChatResponse)
    assert response.content == "Hello from DeepSeek!"
    assert response.model == "deepseek-model"
    assert response.finish_reason == "stop"
    assert isinstance(response.usage, Usage)
    assert response.usage.prompt_tokens == 5
    assert response.usage.completion_tokens == 10
    assert response.usage.total_tokens == 15

    # Проверяем, что OpenAI вызван с правильными аргументами
    mock_openai.return_value.chat.completions.create.assert_called_with(
        model="deepseek-model",
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.7,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

