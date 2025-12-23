import random
from examples import Dates, Times, Locations, People, Events, Urls
from datetime import datetime, timedelta

# dataclasses for generators
dates_ex = Dates()
times_ex = Times()
locations_ex = Locations()
people_ex = People()
events_ex = Events()
urls_ex = Urls()


def sample_date(lang: str = "ru") -> str:
    # relative штучки
    if lang == "ru" and random.random() < 0.15:
        return random.choice(dates_ex.relative_words_ru)

    base = datetime(2025, 12, 6)
    d = base + timedelta(days=random.randint(0, 30))
    if lang == "ru":
        formats = dates_ex.full_date_formats + dates_ex.no_year_formats + dates_ex.text_formats
    else:
        formats = dates_ex.full_date_formats
    return d.strftime(random.choice(formats))


def sample_time(lang: str = "ru") -> str:
    if lang == "ru" and random.random() < 0.2:
        prefix = random.choice(["через", "спустя"])
        amount_num = random.choice(["15", "30", "45", "10", "5", "2"])
        amount_word = random.choice(["минут", "час", "часа", "часов"])

        if random.random() < 0.3:
            return f"{prefix} полчаса"

        return f"{prefix} {amount_num} {amount_word}"

    if lang == "ru" and random.random() < 0.1:
        return random.choice(times_ex.natural_exact_ru)

    h = random.randint(8, 20)
    m = random.choice([0, 15, 30, 45])
    dt = datetime(2025, 1, 1, h, m)
    if lang == "ru":
        formats = times_ex.digital_24h_formats
    else:
        formats = times_ex.digital_12h_formats + times_ex.digital_24h_formats
    return dt.strftime(random.choice(formats))


def sample_place(lang: str = "ru") -> str:
    candidates = []
    if lang == "ru":
        candidates += locations_ex.rooms_ru * 2 + locations_ex.online_ru
    else:
        candidates += locations_ex.rooms_en + locations_ex.online_en
    return random.choice(candidates) if candidates else "office"


def sample_people(lang: str = "ru") -> str:
    candidates = []
    if lang == "ru":
        candidates += people_ex.groups_ru + people_ex.roles_ru + people_ex.names_ru
    else:
        candidates += people_ex.groups_en + people_ex.roles_en + people_ex.names_en
    return random.choice(candidates) if candidates else "team"


def sample_event_name(lang: str = "ru") -> str:
    if lang == "ru":
        type_ = random.choice(events_ex.types_ru)
        if random.random() < 0.3:
            return type_

        proj = random.choice(events_ex.project_names)
        return f"{type_} {proj}"
    else:
        type_ = random.choice(events_ex.types_en)
        topic = random.choice(events_ex.topics_en)
        proj = random.choice(events_ex.project_names)
        return random.choice([
            f"{type_} about {proj}",
            f"{proj} {topic}",
            f"{type_} {topic}",
        ])


def sample_link() -> str:
    key, tmpl = random.choice(list(urls_ex.templates.items()))
    if "{id}" in tmpl:
        return tmpl.format(id=random.randint(10 ** 8, 10 ** 9 - 1))
    if "{code}" in tmpl:
        import string
        letters = string.ascii_lowercase
        code = "".join(random.choice(letters) for i in range(3)) + "-" + "".join(
            random.choice(letters) for j in range(4))
        return tmpl.format(code=code)
    if "{uid}" in tmpl:
        uid = "19:" + "".join(random.choice("0123456789abcdef") for _ in range(30))
        return tmpl.format(uid=uid)
    return tmpl
