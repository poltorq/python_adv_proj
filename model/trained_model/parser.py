import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "data"))

try:
    from examples import Dates
    DATES_CONFIG = Dates()
except ImportError:
    DATES_CONFIG = None


@dataclass
class ParserConfig:
    default_hour: int = 12
    default_minute: int = 0
    
    relative_dates_ru: Dict[str, int] = field(default_factory=lambda: {
        "сегодня": 0,
        "завтра": 1,
        "послезавтра": 2,
        "вчера": -1,
        "позавчера": -2,
    })
    
    weekdays_ru: Dict[str, int] = field(default_factory=lambda: {
        "понедельник": 0, "пн": 0,
        "вторник": 1, "вт": 1,
        "среда": 2, "ср": 2, "среду": 2,
        "четверг": 3, "чт": 3,
        "пятница": 4, "пт": 4, "пятницу": 4,
        "суббота": 5, "сб": 5, "субботу": 5,
        "воскресенье": 6, "вс": 6,
    })
    
    months_ru: Dict[str, int] = field(default_factory=lambda: {
        "январь": 1, "января": 1, "январе": 1, "янв": 1,
        "февраль": 2, "февраля": 2, "феврале": 2, "фев": 2,
        "март": 3, "марта": 3, "марте": 3, "мар": 3,
        "апрель": 4, "апреля": 4, "апреле": 4, "апр": 4,
        "май": 5, "мая": 5, "мае": 5,
        "июнь": 6, "июня": 6, "июне": 6, "июн": 6,
        "июль": 7, "июля": 7, "июле": 7, "июл": 7,
        "август": 8, "августа": 8, "августе": 8, "авг": 8,
        "сентябрь": 9, "сентября": 9, "сентябре": 9, "сен": 9,
        "октябрь": 10, "октября": 10, "октябре": 10, "окт": 10,
        "ноябрь": 11, "ноября": 11, "ноябре": 11, "ноя": 11,
        "декабрь": 12, "декабря": 12, "декабре": 12, "дек": 12,
    })
    
    time_of_day_ru: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        "утро": (9, 0), "утром": (9, 0),
        "день": (14, 0), "днём": (14, 0), "днем": (14, 0),
        "обед": (13, 0), "в обед": (13, 0),
        "вечер": (19, 0), "вечером": (19, 0),
        "ночь": (23, 0), "ночью": (23, 0),
        "полдень": (12, 0),
        "полночь": (0, 0),
    })
    
    relative_time_ru: Dict[str, int] = field(default_factory=lambda: {
        "час": 60,
        "полчаса": 30,
        "минут": 1,
        "минуту": 1,
    })


class DateTimeParser:
    def __init__(
        self, 
        config: Optional[ParserConfig] = None,
        reference_date: Optional[datetime] = None
    ):
        self.config = config or ParserConfig()
        self.reference_date = reference_date or datetime.now()
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.time_patterns = [
            # 15:00, 15:30
            (re.compile(r'^(\d{1,2}):(\d{2})$'), 'HH:MM'),
            # 15.00, 15.30
            (re.compile(r'^(\d{1,2})\.(\d{2})$'), 'HH.MM'),
            # 15-00, 15-30
            (re.compile(r'^(\d{1,2})-(\d{2})$'), 'HH-MM'),
            # 15 часов, 3 часа
            (re.compile(r'^(\d{1,2})\s*(час|часов|часа|ч)\.?$', re.IGNORECASE), 'HH час'),
            # через 15 минут
            (re.compile(r'^через\s+(\d+)\s*(минут|минуты|мин)\.?$', re.IGNORECASE), 'через N мин'),
            # через час
            (re.compile(r'^через\s+(час|полчаса)$', re.IGNORECASE), 'через час'),
        ]
        
        self.date_patterns = [
            # 25.12.2025
            (re.compile(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$'), 'DD.MM.YYYY'),
            # 25/12/2025
            (re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4})$'), 'DD/MM/YYYY'),
            # 25-12-2025
            (re.compile(r'^(\d{1,2})-(\d{1,2})-(\d{4})$'), 'DD-MM-YYYY'),
            # 2025-12-25 (ISO)
            (re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$'), 'YYYY-MM-DD'),
            # 25.12 (без года)
            (re.compile(r'^(\d{1,2})\.(\d{1,2})$'), 'DD.MM'),
            # 25/12 (без года)
            (re.compile(r'^(\d{1,2})/(\d{1,2})$'), 'DD/MM'),
            # 25-12 (без года)
            (re.compile(r'^(\d{1,2})-(\d{1,2})$'), 'DD-MM'),
            # 25 12 (пробел)
            (re.compile(r'^(\d{1,2})\s+(\d{1,2})$'), 'DD MM'),
            # 25 12 2025 (с годом)
            (re.compile(r'^(\d{1,2})\s+(\d{1,2})\s+(\d{4})$'), 'DD MM YYYY'),
            # 25 декабря
            (re.compile(r'^(\d{1,2})\s+([а-яё]+)$', re.IGNORECASE), 'DD месяц'),
            # 25 декабря 2025
            (re.compile(r'^(\d{1,2})\s+([а-яё]+)\s+(\d{4})$', re.IGNORECASE), 'DD месяц YYYY'),
        ]
    
    def parse_date(self, text: str) -> Optional[date]:
        text = text.strip().lower()

        if text in self.config.relative_dates_ru:
            days_offset = self.config.relative_dates_ru[text]
            return (self.reference_date + timedelta(days=days_offset)).date()

        if text in self.config.weekdays_ru:
            return self._next_weekday(self.config.weekdays_ru[text])

        for pattern, format_name in self.date_patterns:
            match = pattern.match(text)
            if match:
                parsed = self._parse_date_match(match, format_name)
                if parsed:
                    return parsed
        
        return None
    
    def _parse_date_match(
        self, 
        match: re.Match, 
        format_name: str
    ) -> Optional[date]:
        try:
            groups = match.groups()
            current_year = self.reference_date.year
            
            if format_name == 'YYYY-MM-DD':
                return date(int(groups[0]), int(groups[1]), int(groups[2]))
            
            elif format_name in ('DD.MM.YYYY', 'DD/MM/YYYY', 'DD-MM-YYYY'):
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
            
            elif format_name == 'DD MM YYYY':
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
            
            elif format_name in ('DD.MM', 'DD/MM', 'DD-MM', 'DD MM'):
                day, month = int(groups[0]), int(groups[1])
                result = date(current_year, month, day)
                if result < self.reference_date.date():
                    result = date(current_year + 1, month, day)
                return result
            
            elif format_name == 'DD месяц':
                day = int(groups[0])
                month_text = groups[1].lower()
                month = self.config.months_ru.get(month_text)
                if month:
                    result = date(current_year, month, day)
                    if result < self.reference_date.date():
                        result = date(current_year + 1, month, day)
                    return result
            
            elif format_name == 'DD месяц YYYY':
                day = int(groups[0])
                month_text = groups[1].lower()
                year = int(groups[2])
                month = self.config.months_ru.get(month_text)
                if month:
                    return date(year, month, day)
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _next_weekday(self, weekday: int) -> date:
        today = self.reference_date.date()
        days_ahead = weekday - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def parse_time(self, text: str) -> Optional[time]:
        text = text.strip().lower()

        if text in self.config.time_of_day_ru:
            hours, minutes = self.config.time_of_day_ru[text]
            return time(hours, minutes)
        
        for pattern, format_name in self.time_patterns:
            match = pattern.match(text)
            if match:
                parsed = self._parse_time_match(match, format_name)
                if parsed:
                    return parsed
        
        return None
    
    def _parse_time_match(
        self, 
        match: re.Match, 
        format_name: str
    ) -> Optional[time]:
        try:
            groups = match.groups()
            
            if format_name in ('HH:MM', 'HH.MM', 'HH-MM'):
                hours, minutes = int(groups[0]), int(groups[1])
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return time(hours, minutes)
            
            elif format_name == 'HH час':
                hours = int(groups[0])
                if 0 <= hours <= 23:
                    return time(hours, 0)
            
            elif format_name == 'через N мин':
                minutes = int(groups[0])
                result_dt = self.reference_date + timedelta(minutes=minutes)
                return result_dt.time()
            
            elif format_name == 'через час':
                word = groups[0].lower()
                minutes = self.config.relative_time_ru.get(word, 60)
                result_dt = self.reference_date + timedelta(minutes=minutes)
                return result_dt.time()
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    def parse(
        self, 
        date_text: Optional[str] = None, 
        time_text: Optional[str] = None
    ) -> Tuple[Optional[date], Optional[time]]:
        parsed_date = None
        parsed_time = None
        
        if date_text:
            parsed_date = self.parse_date(date_text)
        
        if time_text:
            parsed_time = self.parse_time(time_text)
        
        return parsed_date, parsed_time
    
    def parse_datetime(
        self, 
        date_text: Optional[str] = None, 
        time_text: Optional[str] = None
    ) -> Optional[datetime]:
        parsed_date, parsed_time = self.parse(date_text, time_text)
        
        if parsed_date and parsed_time:
            return datetime.combine(parsed_date, parsed_time)
        elif parsed_date:
            default_time = time(self.config.default_hour, self.config.default_minute)
            return datetime.combine(parsed_date, default_time)
        elif parsed_time:
            return datetime.combine(self.reference_date.date(), parsed_time)
        
        return None


def parse_date(text: str, reference: Optional[datetime] = None) -> Optional[date]:
    parser = DateTimeParser(reference_date=reference)
    return parser.parse_date(text)


def parse_time(text: str, reference: Optional[datetime] = None) -> Optional[time]:
    parser = DateTimeParser(reference_date=reference)
    return parser.parse_time(text)


def parse_datetime(
    date_text: Optional[str] = None, 
    time_text: Optional[str] = None,
    reference: Optional[datetime] = None
) -> Optional[datetime]:
    parser = DateTimeParser(reference_date=reference)
    return parser.parse_datetime(date_text, time_text)

