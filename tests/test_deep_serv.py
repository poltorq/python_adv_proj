import pytest
from unittest.mock import Mock

from src.service.deepseek.service import DeepSeekService
from src.clients.deepseek import ChatRequest, Message


class DummyUsage:
    def __init__(self, total, prompt, completion):
        self.total_tokens = total
        self.prompt_tokens = prompt
        self.completion_tokens = completion


class DummyResponse:
    def __init__(self, content="ok", model="test-model", usage=None):
        self.content = content
        self.model = model
        self.usage = usage


@pytest.fixture
def mock_client():
    client = Mock()
    return client


@pytest.fixture
def service(mock_client):
    return DeepSeekService(mock_client)


@pytest.mark.asyncio
async def test_process_meeting_success(service, mock_client):
    mock_client.chat_completion.return_value = DummyResponse(
        content="parsed meeting",
        model="deepseek-test",
        usage=DummyUsage(10, 4, 6),
    )

    result = await service.process_meeting("Meet tomorrow at 10")

    assert result["content"] == "parsed meeting"
    assert result["error"] is None
    assert result["model"] == "deepseek-test"
    assert result["usage"] == {
        "total_tokens": 10,
        "prompt_tokens": 4,
        "completion_tokens": 6,
    }

    mock_client.chat_completion.assert_called_once()
    args, _ = mock_client.chat_completion.call_args
    assert isinstance(args[0], ChatRequest)
    assert isinstance(args[0].messages[0], Message)
    assert args[0].messages[1].content == "Meet tomorrow at 10"


@pytest.mark.asyncio
async def test_process_calendar_success_without_usage(service, mock_client):
    mock_client.chat_completion.return_value = DummyResponse(
        content="calendar help",
        model="deepseek-test",
        usage=None,
    )

    result = await service.process_calendar("What meetings do I have?")

    assert result["content"] == "calendar help"
    assert result["error"] is None
    assert result["model"] == "deepseek-test"
    assert "usage" not in result


@pytest.mark.asyncio
async def test_process_reminder_passes_custom_params(service, mock_client):
    mock_client.chat_completion.return_value = DummyResponse()

    await service.process_reminder(
        "Remind me to call mom",
        temperature=0.9,
        max_tokens=123,
    )

    args, _ = mock_client.chat_completion.call_args
    request = args[0]

    assert request.temperature == 0.9
    assert request.max_tokens == 123


@pytest.mark.asyncio
async def test_process_handles_exception(service, mock_client):
    mock_client.chat_completion.side_effect = RuntimeError("API down")

    result = await service.process_meeting("Any text")

    assert result["content"] is None
    assert result["model"] is None
    assert result["error"] == "API down"
