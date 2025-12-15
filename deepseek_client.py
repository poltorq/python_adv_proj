import os
from typing import Optional

from openai import OpenAI


class DeepSeekClient:
    """
    DeepSeek API client using OpenAI SDK.

    Code works according to the official documentation:
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
         Initializes the DeepSeek API client.

        Args:
            api_key: DeepSeek API key. If not provided, attempts to take it
                from the DEEPSEEK_API_KEY environment variable.
            base_url: Base URL of the API. Default is https://api.deepseek.com.
            model: Model to use. Default is deepseek-chat.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for errors.
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
        Validates the DeepSeek API connection.
        Raises an exception if something is wrong.
        """
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
        except Exception as e:
            raise RuntimeError(
                f"DeepSeek_api_key is not available: {e}"
            ) from e
