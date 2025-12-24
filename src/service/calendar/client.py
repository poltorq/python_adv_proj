from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SimpleGoogleCalendar:
    """Простой клиент для Google Calendar API"""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    def _create_service(self, access_token: str, refresh_token: Optional[str] = None):
        """Создать сервис для работы с API"""
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=['https://www.googleapis.com/auth/calendar']
        )

        # Автообновление токена если нужно
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return build('calendar', 'v3', credentials=creds)

    # ==================== 1. СПИСОК КАЛЕНДАРЕЙ ====================

    def list_calendars(
            self,
            access_token: str,
            refresh_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Вывести список всех календарей пользователя

        Возвращает: [{
            'id': 'календарь@group.calendar.google.com',
            'summary': 'Название календаря',
            'description': 'Описание',
            'primary': True/False
        }]
        """
        service = self._create_service(access_token, refresh_token)

        calendar_list = service.calendarList().list().execute()
        calendars = []

        for cal in calendar_list.get('items', []):
            calendars.append({
                'id': cal['id'],
                'summary': cal.get('summary', 'Без названия'),
                'description': cal.get('description', ''),
                'primary': cal.get('primary', False),
                'time_zone': cal.get('timeZone'),
                'background_color': cal.get('backgroundColor'),
                'foreground_color': cal.get('foregroundColor')
            })

        return calendars

    # ==================== 2. СОБЫТИЯ НА ДЕНЬ ====================

    def list_events_for_day(
            self,
            access_token: str,
            calendar_id: str = "primary",
            date: Optional[str] = None,
            refresh_token: Optional[str] = None,
            timezone: str = "UTC"
    ) -> List[Dict[str, Any]]:
        """
        Вывести список событий на определенный день

        Аргументы:
            date: '2024-12-24' или None (сегодня)

        Возвращает: [{
            'id': 'event_id',
            'summary': 'Название',
            'start': '2024-12-24T10:00:00+03:00',
            'end': '2024-12-24T11:00:00+03:00',
            'status': 'confirmed'
        }]
        """
        service = self._create_service(access_token, refresh_token)

        # Определяем дату
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = datetime.utcnow().date()

        # Формируем временные рамки
        time_min = f"{target_date.isoformat()}T00:00:00{self._format_timezone(timezone)}"
        time_max = f"{target_date.isoformat()}T23:59:59{self._format_timezone(timezone)}"

        # Запрос событий
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,  # Разворачиваем повторяющиеся события
            orderBy='startTime'
        ).execute()

        # Форматируем результат
        events = []
        for event in events_result.get('items', []):
            events.append({
                'id': event['id'],
                'summary': event.get('summary', 'Без названия'),
                'description': event.get('description', ''),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'location': event.get('location', ''),
                'status': event.get('status', 'confirmed'),
                'attendees': len(event.get('attendees', [])),
                'color_id': event.get('colorId')
            })

        return events

    def _format_timezone(self, timezone: str) -> str:
        """Форматирует часовой пояс для API"""
        if timezone == "UTC":
            return "Z"
        return timezone

    # ==================== 3. ИЗМЕНИТЬ СОСТОЯНИЕ СОБЫТИЯ ====================

    def update_event(
            self,
            access_token: str,
            calendar_id: str,
            event_id: str,
            **updates
    ) -> Dict[str, Any]:
        """
        Изменить любое поле события:
        - summary (название)
        - description (описание)
        - start/end (время)
        - location (локация)
        - attendees (участники)
        - recurrence (повторение)
        - и любые другие поля

        Примеры использования:

        1. Изменить название и время:
            update_event(
                access_token, 'primary', 'event_123',
                summary='Новое название встречи',
                start={'dateTime': '2024-12-25T10:00:00+03:00'},
                end={'dateTime': '2024-12-25T11:00:00+03:00'}
            )

        2. Изменить локацию и добавить описание:
            update_event(
                access_token, 'primary', 'event_123',
                location='Новый офис, этаж 5',
                description='Обновленная встреча с командой'
            )

        3. Изменить участников:
            update_event(
                access_token, 'primary', 'event_123',
                attendees=[
                    {'email': 'user1@example.com'},
                    {'email': 'user2@example.com'}
                ]
            )

        4. Изменить время на целый день:
            update_event(
                access_token, 'primary', 'event_123',
                start={'date': '2024-12-25'},
                end={'date': '2024-12-26'}
            )
        """
        service = self._create_service(access_token, updates.get('refresh_token'))

        # Получаем текущее событие
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        # Применяем все обновления
        for key, value in updates.items():
            if key == 'refresh_token':
                continue  # Пропускаем refresh_token, это не поле события

            if value is None:
                # Удаляем поле если передано None
                if key in event:
                    del event[key]
            else:
                # Обновляем поле
                event[key] = value

        # Сохраняем изменения
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()

        return {
            'id': updated_event['id'],
            'summary': updated_event.get('summary'),
            'start': updated_event['start'],
            'end': updated_event['end'],
            'location': updated_event.get('location'),
            'attendees': len(updated_event.get('attendees', [])),
            'updated': updated_event.get('updated')
        }

    # ==================== 4. ДОБАВИТЬ НОВЫЙ КАЛЕНДАРЬ ====================

    def create_calendar(
            self,
            access_token: str,
            name: str,
            description: Optional[str] = None,
            timezone: str = "Europe/Moscow",
            location: Optional[str] = None,
            refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создать новый календарь

        Возвращает: {
            'id': 'новый_календарь@group.calendar.google.com',
            'summary': 'Название',
            'description': 'Описание'
        }
        """
        service = self._create_service(access_token, refresh_token)

        calendar_body = {
            'summary': name,
            'timeZone': timezone
        }

        if description:
            calendar_body['description'] = description
        if location:
            calendar_body['location'] = location

        new_calendar = service.calendars().insert(body=calendar_body).execute()

        return {
            'id': new_calendar['id'],
            'summary': new_calendar['summary'],
            'description': new_calendar.get('description', ''),
            'time_zone': new_calendar['timeZone']
        }

    # ==================== 5. ДОБАВИТЬ НОВОЕ СОБЫТИЕ ====================

    def create_event(
            self,
            access_token: str,
            calendar_id: str,
            title: str,
            start_time: str,
            end_time: str,
            description: Optional[str] = None,
            location: Optional[str] = None,
            attendees: Optional[List[str]] = None,
            timezone: str = "Europe/Moscow",
            refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Добавить новое событие в календарь

        Аргументы:
            start_time/end_time: '2024-12-24T15:00:00' или '2024-12-24'
            timezone: 'Europe/Moscow' или 'UTC'

        Возвращает: созданное событие
        """
        service = self._create_service(access_token, refresh_token)

        # Определяем формат времени (целый день или с временем)
        time_format = 'dateTime' if 'T' in start_time else 'date'

        event_body = {
            'summary': title,
            'start': {
                time_format: start_time,
                'timeZone': timezone
            },
            'end': {
                time_format: end_time,
                'timeZone': timezone
            }
        }

        if description:
            event_body['description'] = description
        if location:
            event_body['location'] = location
        if attendees:
            event_body['attendees'] = [{'email': email} for email in attendees]

        new_event = service.events().insert(
            calendarId=calendar_id,
            body=event_body
        ).execute()

        return {
            'id': new_event['id'],
            'summary': new_event.get('summary', ''),
            'start': new_event['start'].get('dateTime', new_event['start'].get('date')),
            'end': new_event['end'].get('dateTime', new_event['end'].get('date')),
            'html_link': new_event.get('htmlLink')
        }

    # ==================== 6. УДАЛИТЬ СОБЫТИЕ ИЛИ КАЛЕНДАРЬ ====================

    def delete_event(
            self,
            access_token: str,
            calendar_id: str,
            event_id: str,
            refresh_token: Optional[str] = None
    ) -> bool:
        """
        Удалить событие из календаря

        Возвращает: True если успешно
        """
        service = self._create_service(access_token, refresh_token)

        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        return True

    def delete_calendar(
            self,
            access_token: str,
            calendar_id: str,
            refresh_token: Optional[str] = None
    ) -> bool:
        """
        Удалить календарь (не primary!)

        Возвращает: True если успешно
        """
        if calendar_id == "primary":
            raise ValueError("Cannot delete primary calendar")

        service = self._create_service(access_token, refresh_token)

        service.calendars().delete(calendarId=calendar_id).execute()

        return True