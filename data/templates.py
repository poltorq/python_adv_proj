from dataclasses import dataclass
from typing import List


@dataclass
class MessageTemplate:
    ru: str
    en: str
    slots: List[str]


TEMPLATES: List[MessageTemplate] = [
    MessageTemplate(
        ru=(
            "Поставь встречу {event_name} на {date}, где-то в районе {time}, "
            "в {place}, и позови {people}."
        ),
        en=(
            "Set up a meeting {event_name} on {date}, around {time}, "
            "at {place}, and invite {people}."
        ),
        slots=["event_name", "date", "time", "place", "people"],
    ),

    MessageTemplate(
        ru=(
            "Срочно запланируй созвон в {link} {date} примерно в {time}, "
            "хочу обсудить это с {people}."
        ),
        en=(
            "ASAP schedule a call on {link} on {date} around {time}, "
            "I want to discuss this with {people}."
        ),
        slots=["link", "date", "time", "people"],
    ),

    MessageTemplate(
        ru=(
            "Давай сделаем {event_name} {date} в {time}, "
            "где обычно — в {place}."
        ),
        en=(
            "Let's do {event_name} on {date} at {time}, "
            "same place as usual — {place}."
        ),
        slots=["event_name", "date", "time", "place"],
    ),

    MessageTemplate(
        ru="Важный созвон {date}, напомни про него в {time}.",
        en="Serious zoom {date}, remind about it at {time}.",
        slots=["date", "time"],
    ),

    MessageTemplate(
        ru=(
            "Создай, пожалуйста, встречу {event_name} на {date} в {time}, "
            "пригласи туда {people}."
        ),
        en=(
            "Please create a meeting {event_name} on {date} at {time} "
            "and add {people}."
        ),
        slots=["event_name", "date", "time", "people"],
    ),

    MessageTemplate(
        ru=(
            "Перенеси {event_name} на {date}, на {time}, "
            "и поставь это в {place}."
        ),
        en=(
            "Move {event_name} to {date}, {time}, "
            "and put it in {place}."
        ),
        slots=["event_name", "date", "time", "place"],
    ),

    MessageTemplate(
        ru=(
            "Сдвинь нашу встречу {event_name} на пораньше — пусть будет "
            "{time} {date}. Место — {place}."
        ),
        en=(
            "Move our meeting {event_name} earlier — let's make it "
            "{time} on {date}. Location: {place}."
        ),
        slots=["event_name", "time", "date", "place"],
    ),

    MessageTemplate(
        ru=(
            "Отмени, пожалуйста, {event_name}, оно было на {date} "
            "в {time}."
        ),
        en=(
            "Cancel {event_name}, please, it was scheduled for {date} "
            "at {time}."
        ),
        slots=["event_name", "date", "time"],
    ),

    MessageTemplate(
        ru=(
            "Нужно созвониться с {people}. Поставь звонок {date} "
            "на {time} в {link}."
        ),
        en=(
            "Need to call {people}. Set a call on {date} "
            "at {time} in {link}."
        ),
        slots=["people", "date", "time", "link"],
    ),

    MessageTemplate(
        ru=(
            "Забронируй переговорку {place} под {event_name} {date} "
            "в {time}, позови {people}."
        ),
        en=(
            "Book {place} for {event_name} on {date} at {time} "
            "and invite {people}."
        ),
        slots=["place", "event_name", "date", "time", "people"],
    ),

    MessageTemplate(
        ru=(
            "Сделай повторяющуюся встречу {event_name} по {date} "
            "в {time} в {place}."
        ),
        en=(
            "Set up a recurring meeting {event_name} every {date} "
            "at {time} in {place}."
        ),
        slots=["event_name", "date", "time", "place"],
    ),

    MessageTemplate(
        ru=(
            "Добавь в календарь {event_name} {date} в {time}. "
            "Без ссылки, просто отметь."
        ),
        en=(
            "Add {event_name} to the calendar on {date} at {time}. "
            "No link needed, just mark it."
        ),
        slots=["event_name", "date", "time"],
    ),

    MessageTemplate(
        ru=(
            "Назначь короткий созвон {date} в {time} в {link} "
            "с {people}."
        ),
        en=(
            "Set a quick call on {date} at {time} in {link} "
            "with {people}."
        ),
        slots=["date", "time", "link", "people"],
    ),

    MessageTemplate(
        ru=(
            "Хочу встретиться с {people} {date}. Найди время около "
            "{time} и забей в {place}."
        ),
        en=(
            "I want to meet with {people} on {date}. Pick a time around "
            "{time} and book {place}."
        ),
        slots=["people", "date", "time", "place"],
    ),

    MessageTemplate(
        ru=(
            "Можешь придумать, куда воткнуть {event_name}? Давай {date} "
            "в {time}, в {place}."
        ),
        en=(
            "Can you find a slot for {event_name}? Let's say {date} at "
            "{time}, at {place}."
        ),
        slots=["event_name", "date", "time", "place"],
    ),

    MessageTemplate(
        ru=(
            "Напомни мне про {event_name} {date} в {time}, и приложи "
            "ссылку {link}, чтобы не потерялась."
        ),
        en=(
            "Remind me about {event_name} on {date} at {time}, and attach "
            "the link {link} so I don't lose it."
        ),
        slots=["event_name", "date", "time", "link"],
    ),

    MessageTemplate(
        ru=(
            "Создай мне мит {event_name} {date} в {time}, чтобы "
            "созвониться с {people} в {link}."
        ),
        en=(
            "Can you set up a quick {event_name} on {date} at {time} so we "
            "can hop on a call with {people} in {link}?"
        ),
        slots=["event_name", "date", "time", "people", "link"],
    ),

    MessageTemplate(
        ru=(
            "Если можно, сдвинь {event_name} на попозже — на {time} "
            "{date}, место оставь {place}."
        ),
        en=(
            "Please push back {event_name} to {time} on {date}, keep it "
            "in {place}."
        ),
        slots=["event_name", "time", "date", "place"],
    ),

    MessageTemplate(
        ru=(
            "Заблокируй мне время под {event_name} {date} в {time} "
            "в {place} и добавь туда {people}."
        ),
        en=(
            "Block off some time for {event_name} on {date} at {time} in "
            "{place} and loop in {people}."
        ),
        slots=["event_name", "date", "time", "place", "people"],
    ),

    MessageTemplate(
        ru=(
            "Напомни пж про {event_name} ровно {date} в {time} "
            "и позови {people}."
        ),
        en=(
            "Remind pls about {event_name} exactly {date} at {time} "
            "and call {people}."
        ),
        slots=["event_name", "date", "time", "people"],
    ),
]
