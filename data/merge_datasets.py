import json
import re
from datasets import load_dataset, concatenate_datasets
from tqdm import tqdm

LOCAL_DATASET_PATH = "dataset.jsonl"
OUTPUT_PATH = "dataset_full.jsonl"

LIMIT_SYNTHETIC = 9000 # 9к генерим
LIMIT_NOISE = 1000 # 1к шума

TAG_MAPPING = {
    "date": "DATE",
    "time": "TIME",
    "event_name": "TITLE",
    "calendar_name": "TITLE",
    "location": "LOC",
    "place_name": "LOC",
    "person": "USER",
    "relation": "USER",
}


def parse_massive_utt(annot_utt):
    """
    Парсит строку MASSIVE и превращает её в BIO-теги.
    """
    tokens = []
    tags = []
    parts = re.split(r'(\[.*? : .*?\])', annot_utt)
    for part in parts:
        part = part.strip()
        if not part: continue
        match = re.match(r'\[(.*?) : (.*?)\]', part)
        if match:
            raw_label = match.group(1)
            content = match.group(2)
            label = TAG_MAPPING.get(raw_label)
            chunk_tokens = content.split()
            for i, tok in enumerate(chunk_tokens):
                tokens.append(tok)
                if label:
                    tags.append(f"B-{label}" if i == 0 else f"I-{label}")
                else:
                    tags.append("O")
        else:
            chunk_tokens = part.split()
            for tok in chunk_tokens:
                tokens.append(tok)
                tags.append("O")
    return tokens, tags


data_files = {
    "train": "https://huggingface.co/datasets/AmazonScience/massive/resolve/refs/convert/parquet/ru-RU/train/0000.parquet",
    "validation": "https://huggingface.co/datasets/AmazonScience/massive/resolve/refs/convert/parquet/ru-RU/validation/0000.parquet",
    "test": "https://huggingface.co/datasets/AmazonScience/massive/resolve/refs/convert/parquet/ru-RU/test/0000.parquet"
}
dataset_dict = load_dataset("parquet", data_files=data_files)
full_dataset = concatenate_datasets([dataset_dict["train"], dataset_dict["validation"], dataset_dict["test"]])

# CALENDAR SAMPLES
if isinstance(full_dataset[0]["scenario"], int):
    calendar_data = full_dataset.filter(lambda x: x["scenario"] == 2)
    other_data = full_dataset.filter(lambda x: x["scenario"] != 2)
else:
    calendar_data = full_dataset.filter(lambda x: str(x["scenario"]) == "2")
    other_data = full_dataset.filter(lambda x: str(x["scenario"]) != "2")

print(f'calendar_len : {len(calendar_data)}')

# NOISE
if len(other_data) > LIMIT_NOISE:
    noise_data = other_data.shuffle(seed=42).select(range(LIMIT_NOISE))
else:
    noise_data = other_data

print(f'noise_len : {len(noise_data)}')

final_data = []

synthetic_count = 0
with open(LOCAL_DATASET_PATH, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            entry = json.loads(line)
            if entry.get("lang") == "ru":
                final_data.append(entry)
                synthetic_count += 1

            if synthetic_count >= LIMIT_SYNTHETIC:
                break
print(f'generated_len: {synthetic_count}')

# parsiong calendar
for row in tqdm(calendar_data):
    annot_utt = row.get("annot_utt")
    if not annot_utt: continue
    try:
        tokens, new_tags = parse_massive_utt(annot_utt)
        final_data.append({
            "id": int(row["id"]) if "id" in row else 0,
            "lang": "ru",
            "text": " ".join(tokens),
            "tokens": tokens,
            "ner_tags": new_tags,
            "slots": {}
        })
    except Exception as e:
        continue

# parsing noise
for row in tqdm(noise_data):
    text = row.get("utt")
    if not text: continue

    tokens = text.split()
    new_tags = ["O"] * len(tokens)

    final_data.append({
        "id": int(row["id"]) if "id" in row else 0,
        "lang": "ru",
        "text": text,
        "tokens": tokens,
        "ner_tags": new_tags,
        "slots": {}
    })

print(f'final_len : {len(final_data)}')
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for entry in final_data:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"done, full dataset at {OUTPUT_PATH}")
