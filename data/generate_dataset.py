import json
import random
import re
from typing import List, Dict, Tuple, Any
from templates import TEMPLATES, MessageTemplate
from generators import sample_date, sample_time, sample_people, sample_link, sample_place, sample_event_name

random.seed(42)
# mapping and slots stuff
SLOT_TO_TAG = {
    "event_name": "TITLE",
    "place": "LOC",
    "people": "USER",
    "link": "URL",
    "date": "DATE",
    "time": "TIME"
}


def get_slot_value(slot: str, lang: str) -> str:
    if slot == "date": return sample_date(lang)
    if slot == "time": return sample_time(lang)
    if slot == "place": return sample_place(lang)
    if slot == "people": return sample_people(lang)
    if slot == "event_name": return sample_event_name(lang)
    if slot == "link": return sample_link()
    return "UNKNOWN"


# helpers
def tokenizer(text: str) -> List[Tuple[str, int, int]]:
    """
    Decomposition and tokenization of input text
    return: (token, start_pos, ens_pos).
    """
    tokens = []
    #  Matches whole words (\w+) / single punctuation marks ([^\w\s]), skip whitespace
    for match in re.finditer(r'\w+|[^\w\s]', text):
        tokens.append((match.group(), match.start(), match.end()))
    return tokens


def generate_slot_values(template: MessageTemplate, lang: str) -> Dict[str, str]:
    """
    Generate slot values from templates
    """
    return {slot: get_slot_value(slot, lang) for slot in template.slots}


def build_text_with_spans(raw_text: str, slot_values: Dict[str, str]) -> Tuple[str, List[Dict]]:
    """
    Parsing text and evaluating coords of entities
    returns: (text, entities)
    """
    entities = []
    built_text = ""
    current_pos = 0

    # Splitting into slots and the rest of the text
    parts = re.split(r'({.*?})', raw_text)

    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            slot_name = part[1:-1]
            if slot_name in slot_values:
                val = str(slot_values[slot_name])
                start = current_pos
                end = current_pos + len(val)
                tag_label = SLOT_TO_TAG.get(slot_name,
                                            slot_name.upper())

                entities.append({
                    "start": start,
                    "end": end,
                    "label": tag_label
                })

                built_text += val
                current_pos += len(val)
                continue

        built_text += part
        current_pos += len(part)

    return built_text, entities


def create_bio_tags(tokens_with_offsets: List[Tuple[str, int, int]], entities: List[Dict]) -> List[str]:
    """
    Накладывает сущности на токены и формирует BIO-теги.
    """
    tags = ["O"] * len(tokens_with_offsets)

    for entity in entities:
        ent_start = entity["start"]
        ent_end = entity["end"]
        label = entity["label"]

        # Флаг, чтобы первый токен сущности всегда был B-, даже если координаты чуть сбиты
        b_tag_set = False

        for i, (tok_text, tok_start, tok_end) in enumerate(tokens_with_offsets):
            # Проверяем пересечение токена и сущности
            if tok_start < ent_end and tok_end > ent_start:
                if not b_tag_set:
                    tags[i] = f"B-{label}"
                    b_tag_set = True
                else:
                    tags[i] = f"I-{label}"

    return tags


def generate_and_tokenize(template: MessageTemplate, lang: str = "ru") -> Dict[str, Any]:
    """
    Creating a json package of data
    returns dict of data (id, lang, text, tokens, ner_tags, slots)
    """
    raw_text = template.ru if lang == "ru" else template.en

    slot_values = generate_slot_values(template, lang)
    final_text, entities = build_text_with_spans(raw_text, slot_values)

    tokens_with_offsets = tokenizer(final_text)
    tokens = [t[0] for t in tokens_with_offsets]

    ner_tags = create_bio_tags(tokens_with_offsets, entities)

    return {
        "id": random.randint(100000, 999999),
        "lang": lang,
        "text": final_text,
        "tokens": tokens,
        "ner_tags": ner_tags,
        "slots": slot_values
    }


N = 10000 # num of samples
output_file = "dataset.jsonl"
print("generation started")
with open(output_file, "w") as f:
    for i in range(N):
        tmpl = random.choice(TEMPLATES)
        lang = "ru" # now use only ruBERT

        example_data = generate_and_tokenize(tmpl, lang)
        f.write(json.dumps(example_data, ensure_ascii=False) + '\n')

print(f"generated successfully (in {output_file})")
