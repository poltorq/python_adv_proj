# test_simple_google_calendar.py
import pytest
from unittest.mock import patch, MagicMock
from src.service.calendar.client import SimpleGoogleCalendar


@pytest.fixture
def client():
    return SimpleGoogleCalendar(client_id="fake_client_id", client_secret="fake_client_secret")


# ==================== 1. Тест списка календарей ====================
@patch("src.service.calendar.client.build")
def test_list_calendars(mock_build, client):
    mock_service = MagicMock()
    mock_service.calendarList().list().execute.return_value = {
        'items': [
            {'id': 'cal1', 'summary': 'Календарь 1', 'primary': True},
            {'id': 'cal2', 'summary': 'Календарь 2'}
        ]
    }
    mock_build.return_value = mock_service

    calendars = client.list_calendars(access_token="fake_token")
    assert len(calendars) == 2
    assert calendars[0]['id'] == 'cal1'
    assert calendars[0]['primary'] is True
    assert calendars[1]['summary'] == 'Календарь 2'


# ==================== 2. Тест событий на день ====================
@patch("src.service.calendar.client.build")
def test_list_events_for_day(mock_build, client):
    mock_service = MagicMock()
    mock_service.events().list().execute.return_value = {
        'items': [
            {'id': 'evt1', 'summary': 'Событие 1',
             'start': {'dateTime': '2024-12-24T10:00:00+03:00'},
             'end': {'dateTime': '2024-12-24T11:00:00+03:00'}}
        ]
    }
    mock_build.return_value = mock_service

    events = client.list_events_for_day(access_token="fake_token", date="2024-12-24")
    assert len(events) == 1
    assert events[0]['id'] == 'evt1'
    assert events[0]['summary'] == 'Событие 1'


# ==================== 3. Тест обновления события ====================
@patch("src.service.calendar.client.build")
def test_update_event(mock_build, client):
    mock_service = MagicMock()
    mock_service.events().get().execute.return_value = {'id': 'evt1'}
    mock_service.events().update().execute.return_value = {
        'id': 'evt1', 'summary': 'Новое название', 'start': {'dateTime': 'start'},
        'end': {'dateTime': 'end'}, 'attendees': [{'email': 'user@example.com'}], 'updated': 'now'
    }
    mock_build.return_value = mock_service

    updated = client.update_event(
        access_token="fake_token",
        calendar_id="primary",
        event_id="evt1",
        summary="Новое название",
        attendees=[{'email': 'user@example.com'}]
    )
    assert updated['summary'] == 'Новое название'
    assert updated['attendees'] == 1


# ==================== 4. Тест создания календаря ====================
@patch("src.service.calendar.client.build")
def test_create_calendar(mock_build, client):
    mock_service = MagicMock()
    mock_service.calendars().insert().execute.return_value = {
        'id': 'new_cal', 'summary': 'Новый календарь', 'timeZone': 'Europe/Moscow'
    }
    mock_build.return_value = mock_service

    calendar = client.create_calendar(access_token="fake_token", name="Новый календарь")
    assert calendar['id'] == 'new_cal'
    assert calendar['summary'] == 'Новый календарь'


# ==================== 5. Тест создания события ====================
@patch("src.service.calendar.client.build")
def test_create_event(mock_build, client):
    mock_service = MagicMock()
    mock_service.events().insert().execute.return_value = {
        'id': 'evt1', 'summary': 'Событие', 'start': {'dateTime': 'start'},
        'end': {'dateTime': 'end'}, 'htmlLink': 'link'
    }
    mock_build.return_value = mock_service

    event = client.create_event(
        access_token="fake_token",
        calendar_id="primary",
        title="Событие",
        start_time="2024-12-24T10:00:00",
        end_time="2024-12-24T11:00:00"
    )
    assert event['id'] == 'evt1'
    assert event['summary'] == 'Событие'


# ==================== 6. Тест удаления события ====================
@patch("src.service.calendar.client.build")
def test_delete_event(mock_build, client):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    result = client.delete_event(access_token="fake_token", calendar_id="primary", event_id="evt1")
    assert result is True
    mock_service.events().delete().execute.assert_called_once()


# ==================== 7. Тест удаления календаря ====================
@patch("src.service.calendar.client.build")
def test_delete_calendar(mock_build, client):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    result = client.delete_calendar(access_token="fake_token", calendar_id="cal123")
    assert result is True
    mock_service.calendars().delete().execute.assert_called_once()

    # Удаление primary должно вызывать ValueError
    with pytest.raises(ValueError):
        client.delete_calendar(access_token="fake_token", calendar_id="primary")
