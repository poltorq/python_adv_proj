import pytest

from fallback.fallback_logic import (
    is_valid_response,
    build_messages,
    MockModel,
    Message
)

from fallback.fallbacks import (
    empty_response,
    low_quality_output,
    model_has_hallucinations_in_answer,
    model_dont_understand_task,
    model_get_big_and_hard_question,
    model_not_enough_context,
    model_get_provative_or_sensitive_question,
    incorrect_formatt_of_response, 
    model_use_incorrect_type_of_tools,
    user_waited_another_model_response,
)

def test_valid_response():
    prompt = "Объясни, что делает метод strip() в Python."
    text = "Метод strip() удаляет пробелы в начале и конце строки."
    assert is_valid_response(text, prompt, None) == Message(text, "good", None)


def test_empty_response():
    prompt = "Расскажи мне что-нибудь интересное."
    assert is_valid_response("", prompt, None) == build_messages(empty_response() + prompt, "regenerate", None)


def test_whitespace_only_response():
    prompt = "Расскажи мне что-нибудь интересное."
    assert is_valid_response("   \n\t   ", prompt, None) == build_messages(empty_response() + prompt, "regenerate", None)

def test_low_quality_response():
    prompt = "Что такое искусственный интеллект?"
    text = "Да."
    assert is_valid_response(text, prompt, None) == build_messages(low_quality_output() + prompt, "regenerate", None)

def test_refusal_response():
    prompt = "Напиши мне красивый код."
    text = "Извините, но я не могу помочь с этим."
    assert is_valid_response(text, prompt, None) == build_messages(model_dont_understand_task() + prompt, "regenerate", None)

def test_refusal_response_case_insensitive():
    prompt = "Напиши мне красивый код."
    text = "Я НЕ МОГУ ПОМОЧЬ С ЭТИМ"
    assert is_valid_response(text, prompt, None) == build_messages(model_dont_understand_task() + prompt, "regenerate", None)

def test_with_mock_model():
    model = MockModel(behavior="ok")
    prompt = "Какой сегодня день?"
    answer = model.get_answer(prompt)
    assert is_valid_response(answer, prompt, None) == build_messages(answer, "good", None)

    model = MockModel(behavior="empty")
    answer = model.get_answer(prompt)
    assert is_valid_response(answer, prompt, None) == build_messages(empty_response() + prompt, "regenerate", None)
    
    model = MockModel(behavior="hallucination")
    answer = model.get_answer(prompt)
    assert is_valid_response(answer, prompt, None) == build_messages(
        model_has_hallucinations_in_answer() + prompt,
        "regenerate",
        None
    )

    model = MockModel(behavior="refusal")
    answer = model.get_answer("Расскажи мне секретную информацию.")
    assert is_valid_response(answer, prompt, None) == build_messages(
        model_dont_understand_task() + prompt,
        "regenerate",
        None
    )

def should_fallback(text: str, keywords: set[str]) -> bool:
    if not text.strip():
        return True
    if "I can't help" in text:
        return True
    lowered_text = text.lower()
    for phrase in [
        "it is well known that",
        "research shows",
        "studies indicate",
        "experts agree",
    ]:
        if phrase in lowered_text:
            return True
    for keyword in keywords:
        if keyword.lower() in lowered_text:
            return False
    return False

@pytest.mark.parametrize(
    "text,expected",
    [
        ("", True),
        ("   ", True),
        ("I can't help with that.", True),
        ("Experts agree that Python is magic.", True),
        ("Метод strip() удаляет пробелы.", False),
    ],
)
def test_should_fallback_parametrized(text, expected):
    keywords = {"python", "strip"}
    assert should_fallback(text, keywords) is expected

