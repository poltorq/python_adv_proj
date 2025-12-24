from dataclasses import dataclass, field, asdict
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class EntityType(str, Enum):
    DATE = "DATE"
    TIME = "TIME"
    LOCATION = "LOC"
    TITLE = "TITLE"
    USER = "USER"
    URL = "URL"


@dataclass
class NEREntity:
    """
    Сущность, извлечённая NER-моделью.
    
    Attributes:
        entity_type: Тип сущности (DATE, TIME, LOC, TITLE, USER, URL)
        text: Оригинальный текст сущности
        score: Уверенность модели (0-1)
        start: Начальная позиция в тексте
        end: Конечная позиция в тексте
        is_valid: Флаг валидности после проверки
    """
    entity_type: str
    text: str
    score: float
    start: int = 0
    end: int = 0
    is_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedDateTime:
    """
    Разобранная дата/время.
    
    Attributes:
        date_value: Разобранная дата (если есть)
        time_value: Разобранное время (если есть)
        original_text: Оригинальный текст
        is_relative: Флаг относительной даты (завтра, послезавтра)
    """
    date_value: Optional[date] = None
    time_value: Optional[time] = None
    original_text: str = ""
    is_relative: bool = False
    
    @property
    def datetime_value(self) -> Optional[datetime]:
        """Объединённое значение datetime."""
        if self.date_value and self.time_value:
            return datetime.combine(self.date_value, self.time_value)
        elif self.date_value:
            return datetime.combine(self.date_value, time(0, 0))
        elif self.time_value:
            return datetime.combine(date.today(), self.time_value)
        return None
    
    def to_iso_date(self) -> Optional[str]:
        """Дата в формате ISO (YYYY-MM-DD)."""
        return self.date_value.isoformat() if self.date_value else None
    
    def to_iso_time(self) -> Optional[str]:
        """Время в формате ISO (HH:MM:SS)."""
        return self.time_value.isoformat() if self.time_value else None


@dataclass
class EventSlots:
    """
    Слоты события — извлечённые сущности после обработки.
    
    Attributes:
        event_name: Название события (TITLE)
        date_raw: Сырое значение даты из текста
        time_raw: Сырое значение времени из текста
        date_parsed: Разобранная дата
        time_parsed: Разобранное время
        location: Место проведения (LOC)
        participants: Список участников (USER)
        url: Ссылка на встречу (URL)
    """
    event_name: Optional[str] = None
    date_raw: Optional[str] = None
    time_raw: Optional[str] = None
    date_parsed: Optional[date] = None
    time_parsed: Optional[time] = None
    location: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    url: Optional[str] = None
    
    @property
    def datetime_parsed(self) -> Optional[datetime]:
        """Объединённое datetime значение."""
        if self.date_parsed and self.time_parsed:
            return datetime.combine(self.date_parsed, self.time_parsed)
        elif self.date_parsed:
            return datetime.combine(self.date_parsed, time(0, 0))
        elif self.time_parsed:
            return datetime.combine(date.today(), self.time_parsed)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь."""
        return {
            "event_name": self.event_name,
            "date_raw": self.date_raw,
            "time_raw": self.time_raw,
            "date_parsed": self.date_parsed.isoformat() if self.date_parsed else None,
            "time_parsed": self.time_parsed.isoformat() if self.time_parsed else None,
            "datetime": self.datetime_parsed.isoformat() if self.datetime_parsed else None,
            "location": self.location,
            "participants": self.participants,
            "url": self.url,
        }


@dataclass
class EventData:
    """
    Финальная структура события для отправки на бэкенд.
    
    Attributes:
        original_text: Оригинальный текст запроса
        slots: Извлечённые слоты события
        raw_entities: Сырые сущности от модели
        is_valid: Флаг валидности события
        validation_errors: Список ошибок валидации
        created_at: Время создания
    """
    original_text: str
    slots: EventSlots
    raw_entities: List[NEREntity] = field(default_factory=list)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для JSON."""
        return {
            "original_text": self.original_text,
            "slots": self.slots.to_dict(),
            "raw_entities": [e.to_dict() for e in self.raw_entities],
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat(),
        }
    
    def to_json(self, **kwargs) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, **kwargs)
    
    def to_backend_format(self) -> Dict[str, Any]:
        """
        Формат для отправки на бэкенд.
        Минимальный набор данных.
        """
        result = {
            "title": self.slots.event_name or "Новое событие",
            "datetime": None,
            "date": None,
            "time": None,
            "location": self.slots.location,
            "participants": self.slots.participants,
            "url": self.slots.url,
        }
        
        if self.slots.datetime_parsed:
            result["datetime"] = self.slots.datetime_parsed.isoformat()
            result["date"] = self.slots.date_parsed.isoformat() if self.slots.date_parsed else None
            result["time"] = self.slots.time_parsed.isoformat() if self.slots.time_parsed else None
        
        return result

