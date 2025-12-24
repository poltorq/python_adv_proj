from abc import ABC, abstractmethod
from datetime import datetime
import random
import os
import src.clients.deepseek.client as deep_client
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
    '''
    def __init__(self, model: BaseModel):
        self.model = model
        self.deepspeak_model = deep_client.DeepSeekClient(deep_client.AppConfig(
            bot={
                "token": os.getenv("TELEGRAM_TOKEN"),
                "admins": [],
                "use_webhook": False
            },
            deepseek=deep_client.DeepSeekConfig(api_key=os.getenv("DEEPSEEK_API_KEY")),
            debug=True,
            log_level="INFO"
        ))

    def run(self, request: deep_client.ChatRequest, prompt: deep_client.Message) -> dict[str, str]:
        # Ideal structure for validation
        ideal_structure = {
            "title": "встреча",
            "date": "2025-04-25",
            "time": "18:00:00",
            "loc": "офис",
            "user": "Сема",
            "url": "https://zoom.us/..."
        }

        # Get response from the custom model
        custom_response = self.model.get_answer(prompt)

        # Get response from DeepSeek
        deepseek_response = {}
        try:
            self.deepspeak_model.validate_connection()
            deepseek_response = self.deepspeak_model.chat_completion(request).content
        except RuntimeError as e:
            print(f"DeepSeek API error: {e}")

        # Validate responses against the ideal structure
        def validate_response(response):
            return (
                "title" in response and response["title"] and
                "date" in response and is_valid_date(response["date"])
            )

        custom_valid = validate_response(custom_response)

        # Compare and select the best response
        if custom_valid:
            # If DeepSeek response has more values, prioritize it
            if len(deepseek_response) > len(custom_response):
                return deepseek_response
            return custom_response
        else:
            # If custom response is invalid, return DeepSeek response
            return deepseek_response

