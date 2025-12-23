from abc import ABC, abstractmethod
from datetime import datetime
import random

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

    def get_answer(self, prompt: str, system_prompt: str | None = None) -> str:
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


class Answer:
    '''
    {
        "title": "встреча",        // Название события
        "date": "2025-04-25",      // Дата (в формате YYYY-MM-DD)
        "time": "18:00:00",        // Время (в формате HH:MM:SS)
        "loc": "офис",             // Место проведения
        "user": "Сема",            // Участники
        "url": "https://zoom.us/..." // Ссылка (если есть)
    }
    '''
    def __init__(self):
        self.event = dict()
        self.required_fields = ["title", "date", "time", "loc", "user"]

    def is_valid_date(self) -> bool:
        try:
            datetime.strptime(self.event["date"], "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_valid_time(self) -> bool:
        try:
            datetime.strptime(self.event["time"], "%H:%M:%S")
            return True
        except ValueError:
            return False
    
    def add_answer(self, answer):
        self.event["title"] = answer.get("title", "")
        self.event["date"] = answer.get("date", "")
        self.event["time"] = answer.get("time", "")
        self.event["loc"] = answer.get("loc", "")
        self.event["user"] = answer.get("user", "")
        self.event["url"] = answer.get("url", "")
    
    def is_valid(self):
        for field in self.required_fields:
            if field not in self.event or not self.event[field]:
                return False

        if self.is_valid_date() is False:
            return False
        if self.is_valid_time() is False:
            return False

        return True
    def __eq__(self, other):
        return (
            self.event == other.event
        )
    def __ne__(self, value):
        return not self.__eq__(value)


class Message:
    def __init__(self, _user_content: Answer | str, _type: str, _system_content: str | None):
        '''
        Если type = good -> _user_content = answer_for_user_promt(Answer),
        иначе _user_content = promt_for_deep seek
        '''
        self.user_content = _user_content
        self.system_content = _system_content
        self.type = _type

    def __eq__(self, other):
        return (
            self.user_content == other.user_content and
            self.system_content == other.system_content and
            self.type == other.type
        )
    def __ne__(self, value):
        return not self.__eq__(value)


def build_messages(user_prompt: str, type_of_prompt: str, system_prompt: str | None) -> Message:
    message = Message(user_prompt, type_of_prompt, system_prompt)
    return message


def is_valid_response(text: Answer, prompt: str, _system_prompt: str | None = None) -> Message:
    if not text.check():
        return build_messages(prompt, "regenerate", _system_prompt)
    return build_messages(text, "good", _system_prompt)

class FallbackManager:
    '''
        Менеджер для генерации ответов с помощью нашей модели, 
        проверка качества ответа и обращение к модели дипсика,
        если возникают проблемы.
    '''
    def __init__(self, model: BaseModel, deepspeak_model: BaseModel):
        self.model = model
        self.deepspeak_model = deepspeak_model

    def run(self, prompt: str, system_prompt: str | None = None) -> str:
        response = self.model.get_answer(prompt)

        mess = is_valid_response(response, system_prompt)

        if mess.type == "good":
            return mess.user_content
        else:
            return self.deepspeak_model.get_answer(prompt)