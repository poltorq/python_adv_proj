import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv

import pytest

import deepseek_client
from deepseek_client import DeepSeekClient


@patch("deepseek_client.OpenAI")
def test_client_init_with_api_key(mock_openai):
    """Test client creation with API key"""
    mock_client_instance = Mock()
    mock_openai.return_value = mock_client_instance
    mock_client_instance.chat.completions.create.return_value = Mock()

    client = deepseek_client.DeepSeekClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.model == "tngtech/deepseek-r1t-chimera:free"


def test_client_init_without_api_key():
    """Test error when API key is missing"""
    old_key = os.environ.get("DEEPSEEK_API_KEY")

    try:
        if "DEEPSEEK_API_KEY" in os.environ:
            del os.environ["DEEPSEEK_API_KEY"]

        with pytest.raises(
                ValueError, match="Deepseek_api_key is not provided"
        ):
            DeepSeekClient()
    finally:
        if old_key is not None:
            os.environ["DEEPSEEK_API_KEY"] = old_key


@patch("deepseek_client.OpenAI")
def test_init_with_env_variable(mock_openai):
    """Test client creation with key from environment variable"""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock()
    mock_openai.return_value = mock_client

    os.environ["DEEPSEEK_API_KEY"] = "test_key"

    client = DeepSeekClient()
    assert client.api_key == "test_key"


@patch("deepseek_client.OpenAI")
def test_init_parameter_over_environment(mock_openai):
    """Test parameter priority over environment variable"""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock()
    mock_openai.return_value = mock_client

    os.environ["DEEPSEEK_API_KEY"] = "env_key"

    client = DeepSeekClient(api_key="param_key")
    assert client.api_key == "param_key"


@patch("deepseek_client.OpenAI")
def test_custom_parameters(mock_openai):
    """Test custom parameters"""
    mock_client_instance = Mock()
    mock_openai.return_value = mock_client_instance
    mock_client_instance.chat.completions.create.return_value = Mock()

    client = DeepSeekClient(
        api_key="key",
        model="test-model",
        timeout=30,
        max_retries=5,
    )

    assert client.model == "test-model"


@patch("deepseek_client.OpenAI")
def test_openai_client_initialization(mock_openai):
    """Test OpenAI client initialization"""
    mock_client = Mock()
    mock_openai.return_value = mock_client

    DeepSeekClient(api_key="test_key")

    mock_openai.assert_called_once_with(
        api_key="test_key",
        base_url="https://openrouter.ai/api/v1",
        timeout=10,
        max_retries=3,
    )


@patch("deepseek_client.OpenAI")
def test_validate_connection_success(mock_openai):
    """Test successful connection validation"""
    mock_client_instance = Mock()
    mock_openai.return_value = mock_client_instance

    mock_response = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_response

    client = DeepSeekClient(api_key="test_key")

    mock_client_instance.chat.completions.create.reset_mock()

    client.validate_connection()

    mock_client_instance.chat.completions.create.assert_called_once_with(
        model="tngtech/deepseek-r1t-chimera:free",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=1,
    )


@patch("deepseek_client.OpenAI")
def test_validate_connection_failure(mock_openai):
    """Test failed connection validation"""
    mock_client_instance = Mock()
    mock_openai.return_value = mock_client_instance

    mock_client_instance.chat.completions.create.side_effect = [
        Mock(),
        Exception("API Error"),
    ]

    client = DeepSeekClient(api_key="test_key")

    with pytest.raises(
            RuntimeError, match="DeepSeek_api_key is not available"
    ):
        client.validate_connection()


@patch("deepseek_client.OpenAI")
def test_init_calls_validate(mock_openai):
    """Test that __init__ calls validate_connection"""
    mock_client_instance = Mock()
    mock_openai.return_value = mock_client_instance

    with patch.object(DeepSeekClient, "validate_connection") as mock_validate:
        mock_validate.return_value = None

        DeepSeekClient(api_key="test_key")
        mock_validate.assert_called_once()


@patch("deepseek_client.OpenAI")
def test_validate_connection_raises_runtime_error(mock_openai):
    mock_instance = Mock()
    mock_openai.return_value = mock_instance
    mock_instance.chat.completions.create.side_effect = Exception(
        "Network error"
    )

    client = DeepSeekClient.__new__(DeepSeekClient)
    client.client = mock_instance
    client.model = "tngtech/deepseek-r1t-chimera:free"
    client.api_key = "fake_key"

    with pytest.raises(
            RuntimeError,
            match="DeepSeek_api_key is not available: Network error",
    ):
        client.validate_connection()


load_dotenv()


def test_if_it_actually_works():
    """No joking: real test if all this
    code works & produces answers"""
    client = DeepSeekClient()

    response = client.client.chat.completions.create(
        model=client.model,
        messages=[{"role": "user", "content": "Hello, DeepSeek!"}],
        max_tokens=1,
    )

    print(response)
