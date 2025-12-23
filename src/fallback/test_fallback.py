import pytest

from fallback.fallback_logic import (
    is_valid_response,
    build_messages,
    BaseModel,
    MockModel,
    Answer,
    Message
)

def test_MockModel_mock():
    model = MockModel("ok")
    prompt = "Test prompt"
    system_prompt = "System prompt"

    answer = model.get_answer(prompt, system_prompt)

    assert answer == dict(
                title="встреча",
                date="2025-04-25",
                time="18:00:00",
                loc="офис",
                user="Сема",
                url="https://zoom.us/..."
            )
    
    model = MockModel("empty")
    answer = model.get_answer(prompt, system_prompt)
    assert answer == dict()

    model = MockModel("hallucination")
    answer = model.get_answer(prompt, system_prompt)
    assert answer in model.diff_hall

    model = MockModel("shit")
    with pytest.raises(RuntimeError):
        model.get_answer(prompt, system_prompt)

    assert model.generate(prompt, prompt) == "Generated response based on prompt: " + prompt

def test_date_validation_func():
    valid_dates = [
        "2023-10-05",
        "1999-12-31",
        "2000-01-01"
    ]

    invalid_dates = [
        "2023-13-05",  # Invalid month
        "2023-00-10",  # Invalid month
        "2023-02-30",  # Invalid day
        "abcd-ef-gh",  # Non-numeric
        "20231005"    # Wrong format
    ]

    for date in valid_dates:
        answer = Answer()
        answer.event["date"] = date
        assert answer.is_valid_date() == True

    for date in invalid_dates:
        answer = Answer()
        answer.event["date"] = date
        assert answer.is_valid_date() == False

def test_time_validation_func():
    valid_times = [
        "12:30:45",
        "00:00:00",
        "23:59:59"
    ]

    invalid_times = [
        "24:00:00",  # Invalid hour
        "12:60:30",  # Invalid minute
        "12:30:61",  # Invalid second
        "ab:cd:ef",  # Non-numeric
        "12-30-45"   # Wrong format
    ]

    for time in valid_times:
        answer = Answer()
        answer.event["time"] = time
        assert answer.is_valid_time() == True

    for time in invalid_times:
        answer = Answer()
        answer.event["time"] = time
        assert answer.is_valid_time() == False

def test_Answer_validation():
    ans = MockModel("ok").get_answer("fjsdjf", "fjdfjfs")
    answer = Answer()
    answer.add_answer(ans)
    assert answer.is_valid() == True 

    ans = MockModel("hallucination").get_answer("fjsdjf", "fjdfjfs")
    answer.add_answer(ans)
    assert answer.is_valid() == False

    answer.add_answer(dict(title="встреча"))
    assert answer.is_valid() == False


