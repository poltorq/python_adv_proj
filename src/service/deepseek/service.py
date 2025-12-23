from typing import Dict, Any
from src.clients.deepseek import DeepSeekClient, ChatRequest, Message
from src.service.deepseek import prompts


class DeepSeekService:
    def __init__(self, deepseek_client: DeepSeekClient):
        self.client = deepseek_client
        self._prompts = prompts

    @property
    def meeting_parser_prompt(self) -> str:
        return self._prompts.MEETING_PARSER_PROMPT

    @property
    def calendar_assistant_prompt(self) -> str:
        return self._prompts.CALENDAR_ASSISTANT_PROMPT

    @property
    def reminder_parser_prompt(self) -> str:
        return self._prompts.REMINDER_PARSER_PROMPT

    async def process_meeting(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """Парсит сообщение о встрече."""
        return await self._process(self.meeting_parser_prompt, user_message, **kwargs)

    async def process_calendar(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """Помощник по календарю."""
        return await self._process(
            self.calendar_assistant_prompt, user_message, **kwargs
        )

    async def process_reminder(self, user_message: str, **kwargs) -> Dict[str, Any]:
        """Парсит напоминания."""
        return await self._process(self.reminder_parser_prompt, user_message, **kwargs)

    async def _process(
        self, system_prompt: str, user_message: str, **kwargs
    ) -> Dict[str, Any]:
        """Внутренний метод обработки."""
        try:
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_message),
            ]

            request = ChatRequest(
                messages=messages,
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 1000),
            )

            response = self.client.chat_completion(request)

            result = {
                "content": response.content,
                "error": None,
                "model": response.model,
            }

            if response.usage:
                result["usage"] = {
                    "total_tokens": response.usage.total_tokens,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }

            return result

        except Exception as e:
            return {
                "content": None,
                "error": str(e),
                "model": None,
            }
