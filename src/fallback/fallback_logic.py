from abc import ABC, abstractmethod
from fallback.fallbacks import (
    low_quality_output,
    empty_response,
    model_has_hallucinations_in_answer,
    model_dont_understand_task,
    model_get_big_and_hard_question,
    model_not_enough_context,
    model_get_provative_or_sensitive_question,
    incorrect_formatt_of_response,
    model_use_incorrect_type_of_tools,
    user_waited_another_model_response,
    HALLUCINATION_PHRASES,
    MODEL_DONT_ANWER_PHRASES
)

class BaseModel(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        pass


class MockModel(BaseModel):
    def __init__(self, behavior: str):
        self.behavior = behavior

    def get_answer(self, prompt: str) -> str:
        if self.behavior == "ok":
            return "Ответ на запрос: " + prompt

        if self.behavior == "empty":
            return ""

        if self.behavior == "hallucination":
            return "Франция украла флаг у России - это широко известно во всем мире"

        if self.behavior == "refusal":
            return "Я не могу помочь"

        raise RuntimeError("Model crashed")

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Generated response based on prompt: " + prompt


class Message:
    def __init__(self, _user_content: str, _type: str, _system_content: str | None):
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


def is_valid_response(text: str, prompt: str, _system_prompt: str | None = None) -> Message:
    if text.strip() == "":
        return build_messages(empty_response() + prompt, "regenerate", _system_prompt)
    for phrase in MODEL_DONT_ANWER_PHRASES:
        if phrase.lower() in text.lower():
            return build_messages(model_dont_understand_task() + prompt, "regenerate", _system_prompt)
    for phrase in HALLUCINATION_PHRASES:
        if phrase in text.lower():
            return build_messages(model_has_hallucinations_in_answer() + prompt, "regenerate", _system_prompt)
    if len(text) < 10:
        return build_messages(low_quality_output() + prompt, "regenerate", _system_prompt)

    return build_messages(text, "good", _system_prompt)


class FallbackManager:
    def __init__(self, model: BaseModel):
        self.model = model

    def run(self, prompt: str, system_prompt: str | None = None) -> str:
        response = self.model.get_answer(prompt)

        return is_valid_response(response, system_prompt)