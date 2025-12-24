import pytest
from datetime import datetime, timedelta
from src.models.models import UserData


def test_user_data_initialization():
    user = UserData(user_id=1, username="testuser", first_name="John", last_name="Doe")
    assert user.user_id == 1
    assert user.username == "testuser"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert isinstance(user.created_at, datetime)

def test_user_data_default_created_at():
    user = UserData(user_id=2)
    now = datetime.now()
    assert now - timedelta(seconds=1) <= user.created_at <= now

def test_user_data_full_name():
    user = UserData(user_id=3, first_name="Jane", last_name="Smith")
    assert user.full_name == "Jane Smith"

    user = UserData(user_id=4, first_name="Jane")
    assert user.full_name == "Jane"

    user = UserData(user_id=5)
    assert user.full_name == "Аноним"