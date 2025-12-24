# tests/test_serv_serv.py
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

# Устанавливаем переменные окружения до импорта приложения
os.environ["DB_DIALECT"] = "postgresql"
os.environ["DB_NAME"] = "meeting_bot"
os.environ["DB_USER"] = "bot_user"
os.environ["DB_PASSWORD"] = "bot_password123"
os.environ["DB_DRIVER"] = "asyncpg"
os.environ["DB_HOST"] = "213.226.127.133"
os.environ["DB_PORT"] = "6432"

# После этого импортируем app
from src.cmd.server.server import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_async_session():
    with patch("src.cmd.server.server.async_session", new_callable=AsyncMock) as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx
        yield mock_session

def test_auth_google_redirect():
    response = client.get("/auth/google", params={"user_id": "1", "chat_id": "2"})
    assert response.status_code == 404

def test_google_callback_missing_code_state():
    response = client.get("/auth/google/callback")
    assert response.status_code == 400
    assert "missing code/state" in response.json()["error"]

    response = client.get("/auth/google/callback?error=access_denied")
    assert response.status_code == 400
    assert response.json()["error"] == "access_denied"

    response = client.get("/auth/google/callback?code=123&state=invalidstate")
    assert response.status_code == 400
    assert response.json()["error"] == "invalid state"


def test_google_callback_invalid_state():
    response = client.get("/auth/google/callback", params={"code": "test_code", "state": "invalid"})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid state"

