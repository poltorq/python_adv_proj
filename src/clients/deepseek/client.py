import os
from typing import Optional, List
from dataclasses import dataclass
from openai import OpenAI
from src.config.config import AppConfig


@dataclass
class Message:
    """Одно сообщение в диалоге с DeepSeek."""

    role: str  # Роль отправителя: "system", "user" или "assistant"
    content: str  # Текст сообщения


@dataclass
class ChatRequest:
    """Запрос на генерацию ответа от DeepSeek."""

    messages: List[
        Message
    ]  # История диалога (системный промпт + сообщения пользователя)

    # Параметры генерации:
    temperature: float = 0.7  # Креативность ответов (0.0-1.0, где 0 - детерминировано)
    max_tokens: int = 1000  # Максимальная длина ответа в токенах
    top_p: float = 1.0  # Качество выборки (0.0-1.0, где 1 - все варианты)
    frequency_penalty: float = 0.0  # Штраф за частые слова (0.0-2.0)
    presence_penalty: float = 0.0  # Штраф за новые слова (0.0-2.0)


@dataclass
class ChatResponse:
    """Ответ от DeepSeek API."""

    content: str  # Сгенерированный текст ответа
    model: str  # Название модели, которая сгенерировала ответ
    finish_reason: (
        str  # Причина завершения генерации ("stop", "length", "content_filter")
    )
    usage: Optional["Usage"] = None  # Информация об использовании токенов


@dataclass
class Usage:
    """Информация о расходе токенов."""

    prompt_tokens: int  # Токены во входном промпте
    completion_tokens: int  # Токены в сгенерированном ответе
    total_tokens: int  # Всего токенов (prompt + completion)


class DeepSeekClient:
    """
    Клиент для работы с DeepSeek API через OpenAI SDK.

    Используется согласно официальной документации:
    https://api-docs.deepseek.com
    """

    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        """
        Инициализация клиента DeepSeek.

        Args:
            config: Объект конфигурации приложения с настройками DeepSeek.

        Raises:
            ValueError: Если API ключ не предоставлен.
        """
        self.api_key = config.deepseek.api_key
        if not self.api_key:
            raise ValueError("API ключ DeepSeek не предоставлен")

        # Создаем клиент OpenAI с настройками из конфига
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=config.deepseek.base_url,
            timeout=30,  # Таймаут запроса в секундах
            max_retries=3,  # Максимальное количество попыток при ошибках
        )
        self.model = config.deepseek.model  # Модель DeepSeek для использования
        self.validate_connection()  # Проверяем подключение к API

    def validate_connection(self) -> None:
        """
        Проверяет подключение к DeepSeek API.
        Отправляет тестовый запрос "ping".

        Raises:
            RuntimeError: Если подключение не удалось установить.
        """
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek API недоступен: {e}") from e

    def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Отправляет запрос на генерацию текста в DeepSeek API.

        Args:
            request: Объект ChatRequest с историей диалога и параметрами генерации.

        Returns:
            ChatResponse: Объект с ответом от DeepSeek.

        Raises:
            RuntimeError: Если запрос к API завершился ошибкой.
        """
        try:
            # Конвертируем объекты Message в формат словарей для OpenAI API
            messages = [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ]

            # Отправляем запрос к API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
            )

            # Создаем объект Usage, если данные о токенах есть
            usage = None
            if response.usage:
                usage = Usage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            # Возвращаем структурированный ответ
            return ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                usage=usage,
            )

        except Exception as e:
            raise RuntimeError(f"Запрос к DeepSeek API не удался: {e}") from e
