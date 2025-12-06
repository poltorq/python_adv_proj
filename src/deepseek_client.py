import os
from typing import Any, Optional
from openai import OpenAI

class DeepSeekClient:

    """
    Клиент DeepSeek API, использует OpenAI

    Работает по образу и подобию официальной документации:
    https://api-docs.deepseek.com
    """

    def __init__(
            self,
            api_key: Optional[str] = None,
            base_url: str = "https://api.deepseek.com",
            model: str = "deepseek-chat",
            timeout: int = 10,
            max_retries: int = 3,
    ) -> None:
        """
        Тут происходит инициализация клиента DeepSeek API.

        Args:
          api_key: API ключ DeepSeek. Если не указан, происходит попытка взять его из DEEPSEEK_API_KEY.
          base_url: Базовый URL API. По умолчанию https://api.deepseek.com.
          model: Модель для использования. По умолчанию deepseek-chat.
          timeout: Таймаут запроса в секундах.
          max_retries: Максимальное количество повторных попыток при ошибках.
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("Deepseek_api_key is not provided")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.model = model
        self.validate_connection()


    def validate_connection(self) -> None:
        """
        Валидирует работу DeepSeek API.
        Если что-то не так — выкидывает Exception.
        """
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek_api_key is not available: {e}")


