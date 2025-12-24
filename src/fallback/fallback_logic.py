from abc import ABC, abstractmethod
from datetime import datetime
import random
import os

from model import extract_event, format_event_for_display, process_text
import src.clients.deepseek.client as deep_client
from src.clients.deepseek.client import DeepSeekClient
from src.config.config import AppConfig, DeepSeekConfig

class BaseModel(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        pass


class MockModel(BaseModel):
    def __init__(self, behavior: str):
        self.behavior = behavior
        self.diff_hall = [
            dict(title="встреча",
                date="2025-04-25",
                time="18:00:61",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            ),
            dict(title="встреча",
                date="2025-04-25",
                time="25:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            ),
            dict(title="встреча",
                date="2025-04-25",
                time="18:61:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            ),
            dict(title="встреча",
                date="2025-13-25",
                time="18:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            ),
            dict(title="встреча",
                date="2025-04-40",
                time="18:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            )
        ]

    def get_answer(self, prompt: str, system_prompt: str | None = None) -> dict[str, str]:
        if self.behavior == "ok":
            return dict(
                title="встреча",
                date="2025-04-25",
                time="18:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            )

        if self.behavior == "empty":
            return dict()

        if self.behavior == "hallucination":
            return self.diff_hall[random.randint(0, len(self.diff_hall) - 1)]

        raise RuntimeError("Model crashed")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Generated response based on prompt: " + prompt


def is_valid_date(date: str) -> bool:
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_valid_time(time: str) -> bool:
    try:
        datetime.strptime(time, "%H:%M:%S")
        return True
    except ValueError:
        return False

class FallbackManager:
    '''
        Менеджер для генерации ответов с помощью нашей модели, 
        проверка качества ответа и обращение к модели дипсика,
        если возникают проблемы.
        Ideal structure for validation
        ideal_structure = {
            "title": "встреча",
            "date": "2025-04-25",
            "time": "18:00:00",
            "loc": "офис",
            "user": "Сема",
            "url": "https://zoom.us/..."
        }
    '''

    def run(self, request: deep_client.ChatRequest, prompt: deep_client.Message) -> dict[str, str]:
        # Get response from the custom model


        # custom_response = extract_event(prompt.content)
        custom_response = {}

        # Validate responses against the ideal structure
        def validate_response(response):
            return (
                "title" in response and response["title"] and
                "date" in response and is_valid_date(response["date"])
            )

        custom_valid = validate_response(custom_response)

        # Compare and select the best response
        if custom_valid:
            return custom_response
        else:
            try:
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
                self.deepspeak_model = DeepSeekClient(config=config)
                cont= "Преобразуй запрос пользователь в подобный формат: { \
                    \"title\": \"встреча\", \
                    \"date\": \"2025-04-25\", \
                    \"time\": \"18:00:00\", \
                    \"loc\": \"офис\", \
                    \"user\": \"Сема\", \
                    \"url\": \"https://zoom.us/...\" \
                } Вот сам запрос: "
                prompt.content = cont + prompt.content
                request.messages.append(prompt)
                self.deepspeak_model.validate_connection()
                return self.deepspeak_model.chat_completion(request).content
            except Exception:
                return custom_response
