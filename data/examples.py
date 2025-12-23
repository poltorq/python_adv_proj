from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Dates:
    full_date_formats: List[str] = field(default_factory=lambda: [
        "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y", "%Y-%m-%d"
    ])
    no_year_formats: List[str] = field(default_factory=lambda: [
        "%d.%m", "%d/%m", "%d-%m", "%d %m"
    ])
    text_formats: List[str] = field(default_factory=lambda: [
        "%B %d", "%d %b"
    ])
    relative_words_ru: List[str] = field(default_factory=lambda: [
        "сегодня", "завтра", "послезавтра", "позавчера"
    ])

    months_en: List[str] = field(default_factory=lambda: [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ])

    months_ru: Dict[int, List[str]] = field(default_factory=lambda: {
        1: ["январь", "января", "январе", "янв"],
        2: ["февраль", "февраля", "феврале", "фев"],
        3: ["март", "марта", "марте", "мар"],
        4: ["апрель", "апреля", "апреле", "апр"],
        5: ["май", "мая", "мае", "май"],
        6: ["июнь", "июня", "июне", "июн"],
        7: ["июль", "июля", "июле", "июл"],
        8: ["август", "августа", "августе", "авг"],
        9: ["сентябрь", "сентября", "сентябре", "сен"],
        10: ["октябрь", "октября", "октябре", "окт"],
        11: ["ноябрь", "ноября", "ноябре", "ноя"],
        12: ["декабрь", "декабря", "декабре", "дек"]
    })
    months_ru_flat: List[str] = field(init=False)

    def __post_init__(self):
        self.months_ru_flat = [w for forms in self.months_ru.values() for w in forms]


@dataclass
class Times:
    digital_24h_formats: List[str] = field(default_factory=lambda: [
        "%H:%M", "%H.%M", "%H-%M"
    ])
    digital_12h_formats: List[str] = field(default_factory=lambda: [
        "%I:%M %p", "%I:%M%p", "%I %p"
    ])
    natural_exact_ru: List[str] = field(default_factory=lambda: [
        "полдень", "полночь", "утро", "вечер", "обед"
    ])
    natural_exact_en: List[str] = field(default_factory=lambda: [
        "noon", "midnight"
    ])


@dataclass
class Locations:
    prepositions_ru: List[str] = field(default_factory=lambda: [
        "в", "на", "у", "около", "возле"
    ])
    prepositions_en: List[str] = field(default_factory=lambda: [
        "in", "at", "near", "by"
    ])
    online_ru: List[str] = field(default_factory=lambda: [
        "Zoom", "Зум", "Google Meet", "Meet", "Skype", "Скайп",
        "Teams", "Тимс", "онлайн", "по ссылке", "Discord", "Телеграм", "Telegram", "телега"
    ])
    online_en: List[str] = field(default_factory=lambda: [
        "Zoom", "Google Meet", "MS Teams", "Skype", "Discord",
        "online", "remote", "via link"
    ])
    rooms_ru: List[str] = field(default_factory=lambda: [
        "переговорная", "переговорка", "конференц-зал", "актовый зал",
        "кабинет", "офис", "главный офис", "митинг-рум", "аудитория",
        "баня", "сауна", "спортзал", "зал", "тренировка", "бар", "кафе", "ресторан", "курилка"
    ])
    rooms_en: List[str] = field(default_factory=lambda: [
        "Conference Room", "Meeting Room", "Office", "Main Office",
        "Auditorium", "Boardroom", "Hall", "Gym", "Bar"
    ])
    room_identifiers_ru: List[str] = field(default_factory=lambda: [
        "1", "2", "3", "101", "305", "А", "Б", "В", "Главная", "Малая"
    ])
    room_identifiers_en: List[str] = field(default_factory=lambda: [
        "1", "2", "3", "101", "404", "A", "B", "C", "Main", "Small"
    ])


@dataclass
class People:
    groups_ru: List[str] = field(default_factory=lambda: [
        "все", "команда", "отдел маркетинга", "разработчики",
        "HR отдел", "бухгалтерия", "дизайнеры", "QA", "тестировщики",
        "iOS команда", "Android команда", "бэкендеры", "фронты"
    ])
    groups_en: List[str] = field(default_factory=lambda: [
        "all", "team", "marketing", "developers", "devs",
        "HR", "designers", "QA team", "everyone", "board members"
    ])
    roles_ru: List[str] = field(default_factory=lambda: [
        "тимлид", "лид", "менеджер", "заказчик", "стажеры",
        "генеральный", "клиент", "HR", "рекрутер"
    ])
    roles_en: List[str] = field(default_factory=lambda: [
        "Team Lead", "PM", "Product Owner", "CEO", "client", "interns"
    ])
    names_ru: List[str] = field(default_factory=lambda: [
        "Яна", "Милана", "Саша", "Никита", "Даня", "Петр Павлович",
        "Иван", "Алексей", "Мария", "Ольга", "Дмитрий"
    ])
    names_en: List[str] = field(default_factory=lambda: [
        "John", "Peter", "Maria", "Jenson", "Liam", "dr. Pepper"
    ])


@dataclass
class Events:
    types_ru: List[str] = field(default_factory=lambda: [
        "встреча", "созвон", "синк", "дейлик", "летучка", "планерка",
        "собрание", "воркшоп", "демо", "ретро", "ретроспектива",
        "1:1", "one-on-one", "интервью", "собеседование", "миток", "статус", "брифинг", "вебинар"
    ])
    types_en: List[str] = field(default_factory=lambda: [
        "meeting", "sync", "call", "daily", "standup", "weekly",
        "workshop", "demo", "retro", "retrospective",
        "1:1", "check-in", "interview"
    ])
    topics_en: List[str] = field(default_factory=lambda: [
        "project sync", "budget review", "status update",
        "launch", "release", "training"
    ])
    topics_ru: List[str] = field(default_factory=lambda: [
        "синк по проекту", "ревью бюджета", "обновление статуса",
        "запуск", "релиз", "обучение", "анбординг", "планирование"
    ])
    project_names: List[str] = field(default_factory=lambda: [
        "'Ромашка'", "Project X", "MVP", "SuperApp", "Website Redesign",
        "Q1 Goals", "Alpha", "Phoenix", "Black Friday"
    ])


@dataclass
class Urls:
    templates: Dict[str, str] = field(default_factory=lambda: {
        "zoom_full": "https://company.zoom.us/j/{id}",
        "zoom_short": "https://zoom.us/j/{id}",
        "zoom_no_http": "zoom.us/j/{id}",
        "meet_full": "https://meet.google.com/{code}",
        "meet_short": "meet.google.com/{code}",
        "teams_full": "https://teams.microsoft.com/l/meetup-join/{uid}",
    })
    regex_patterns: Dict[str, str] = field(default_factory=lambda: {
        "zoom": r"zoom\.us/j/\d+",
        "meet": r"meet\.google\.com/[a-z-]+",
        "teams": r"teams\.microsoft\.com/.*",
        "url_generic": r"https?://[^\s]+"
    })
    providers: List[str] = field(default_factory=lambda: [
        "zoom.us", "meet.google.com", "teams.microsoft.com",
        "webex.com", "skype.com"
    ])
