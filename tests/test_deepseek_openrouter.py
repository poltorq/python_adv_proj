import os
from openai import base_url
import pytest

from src.clients.deepseek.client import DeepSeekClient, DeepSeekConfig, ChatRequest, Message
import deepseek_client
from src.config.config import AppConfig
from src.fallback.fallback_logic import FallbackManager, MockModel

@pytest.mark.integration
def test_openrouter_deepseek_real_request():
    """
    REAL integration test:
    - sends request to OpenRouter
    - model = DeepSeek
    - expects a real response
    """

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY is not set")

    config = AppConfig(
        bot={
            "token": os.getenv("TELEGRAM_TOKEN"),
            "admins": [],
            "use_webhook": False,
        },
        deepseek=DeepSeekConfig(
            api_key=api_key,
            #base_url="https://openrouter.ai/api/v1",
            #model="tngtech/deepseek-r1t-chimera:free",
            base_url="https://openrouter.ai/api/v1",
            model="nex-agi/deepseek-v3.1-nex-n1:free"
        ),
        debug=True,
        log_level="INFO",
    )

    client = DeepSeekClient(config)

    # если validate_connection() не упал — API реально доступен
    client.validate_connection()

    response = client.client.chat.completions.create(
        model=config.deepseek.model,
        messages=[{"role": "user", "content": "Reply with OK"}],
        max_tokens=5,
    )

    assert response is not None
    assert len(response.choices) > 0
    assert response.choices[0].message.content.strip() != ""

@pytest.mark.integration
def test_if_it_actually_works():
    """No joking: real test if all this
    code works & produces answers"""
    config = AppConfig(
        bot={
            "token": os.getenv("TELEGRAM_TOKEN"),
            "admins": [],
            "use_webhook": False,
        },
        deepseek=DeepSeekConfig(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            #base_url="https://openrouter.ai/api/v1",
            #model="tngtech/deepseek-r1t-chimera:free",
            base_url="https://openrouter.ai/api/v1",
            model="nex-agi/deepseek-v3.1-nex-n1:free"
        ),
        debug=True,
        log_level="INFO",
    )
    client = DeepSeekClient(config)

    response = client.client.chat.completions.create(
        model=client.model,
        messages=[{"role": "user", "content": "Hello, DeepSeek!"}],
        max_tokens=1,
    )

    print(response)

# @pytest.mark.integration
# def test_fallback_manager_real_deepseek_request():
#     model = MockModel("empty")  # Custom model возвращает пустой ответ
#     fallback_manager = FallbackManager(model)

#     user_message = Message(role="user", 
#         content="Преобразуй запрос пользователь в подобный формат: { \
#             \"title\": \"встреча\", \
#             \"date\": \"2025-04-25\", \
#             \"time\": \"18:00:00\", \
#             \"loc\": \"офис\", \
#             \"user\": \"Сема\", \
#             \"url\": \"https://zoom.us/...\" \
#         } \
#         Вот сам запрос: Встреча 2025-04-25 с Семой в офисе в 18:00 по Zoom. Вот ссылка: https://zoom.us/...")
#     chat_request = ChatRequest(messages=[])

#     # Отправляем реальный запрос в DeepSeek API
#     result = fallback_manager.run(chat_request, user_message)

#     # Проверяем, что результат содержит ожидаемые ключи
#     assert "title" in result
#     assert "date" in result
#     assert "time" in result
#     assert "loc" in result
#     assert "user" in result
#     assert "url" in result