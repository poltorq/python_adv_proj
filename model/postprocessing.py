import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, time
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    reason: Optional[str] = None
    cleaned_text: Optional[str] = None


@dataclass
class PostprocessorConfig:
    min_score: float = 0.5
    min_text_length: int = 1
    
    invalid_patterns: List[str] = field(default_factory=lambda: [
        r"^##",      # BERT subword prefix
        r"##$",      # BERT subword suffix
        r"^\[.*\]$", # Special tokens [CLS], [SEP], [PAD]
        r"^[^\w]+$", # Only punctuation
    ])
    
    suspicious_time_patterns: List[str] = field(default_factory=lambda: [
        r"^\d{4}$",
        r"^\d+:\d+:\d+$",
    ])


class NERPostprocessor:
    """
    Постпроцессор NER-результатов.
    Объединяет валидацию, очистку и нормализацию сущностей.
    """
    
    def __init__(self, config: Optional[PostprocessorConfig] = None):
        self.config = config or PostprocessorConfig()
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.invalid_regexes = [re.compile(p) for p in self.config.invalid_patterns]
        self.suspicious_time_regexes = [re.compile(p) for p in self.config.suspicious_time_patterns]
    
    # ==================== ОЧИСТКА ТЕКСТА ====================
    
    def clean_text(self, text: str) -> str:
        """Очищает текст от артефактов BERT-токенизации."""
        cleaned = re.sub(r'\s*:\s*', ':', text)
        cleaned = re.sub(r'\s*/\s*', '/', cleaned)
        cleaned = re.sub(r'\s*\.\s*', '.', cleaned)
        cleaned = re.sub(r'\s*-\s*', '-', cleaned)
        cleaned = re.sub(r'\s*@\s*', '@', cleaned)
        cleaned = re.sub(r'\s*##\s*', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def normalize_url(self, url: str) -> str:
        cleaned = self.clean_text(url)
        if not cleaned.startswith(('http://', 'https://')):
            if cleaned.startswith('//'):
                cleaned = 'https:' + cleaned
            else:
                cleaned = 'https://' + cleaned
        return cleaned
    
    def normalize_time(self, time_str: str) -> Optional[str]:
        cleaned = self.clean_text(time_str)
        patterns = [
            r'^(\d{1,2}):(\d{2})$',
            r'^(\d{1,2})\.(\d{2})$',
            r'^(\d{1,2})-(\d{2})$',
        ]
        for pattern in patterns:
            match = re.match(pattern, cleaned)
            if match:
                hours, minutes = int(match.group(1)), int(match.group(2))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return f"{hours:02d}:{minutes:02d}"
        return None
    
    # ==================== ВАЛИДАЦИЯ ====================
    
    def validate_entity(self, entity_type: str, text: str, score: float) -> ValidationResult:
        if score < self.config.min_score:
            return ValidationResult(False, f"Low score: {score:.3f} < {self.config.min_score}")
        
        cleaned_text = self.clean_text(text)
        
        if len(cleaned_text) < self.config.min_text_length:
            return ValidationResult(False, f"Text too short: '{cleaned_text}'")
        
        for regex in self.invalid_regexes:
            if regex.search(text):
                return ValidationResult(False, f"Invalid pattern: {regex.pattern}")
        
        type_validation = self._validate_by_type(entity_type, cleaned_text, score)
        if not type_validation.is_valid:
            return type_validation
        
        return ValidationResult(True, cleaned_text=cleaned_text)
    
    def _validate_by_type(self, entity_type: str, text: str, score: float) -> ValidationResult:
        if entity_type == "DATE":
            return self._validate_date(text, score)
        elif entity_type == "TIME":
            return self._validate_time(text, score)
        elif entity_type == "URL":
            return self._validate_url(text)
        elif entity_type == "LOC":
            return self._validate_location(text)
        elif entity_type == "USER":
            return self._validate_user(text)
        return ValidationResult(True, cleaned_text=text)
    
    def _validate_date(self, text: str, score: float) -> ValidationResult:
        if re.match(r'^\d{4}$', text) and score < 0.7:
            return ValidationResult(False, f"Suspicious year: {text}")
        return ValidationResult(True, cleaned_text=text)
    
    def _validate_time(self, text: str, score: float) -> ValidationResult:
        for regex in self.suspicious_time_regexes:
            if regex.match(text) and score < 0.7:
                return ValidationResult(False, f"Suspicious time: {text}")
        
        time_match = re.match(r'^(\d{1,2}):(\d{2})$', text)
        if time_match:
            hours, minutes = int(time_match.group(1)), int(time_match.group(2))
            if hours > 23 or minutes > 59:
                return ValidationResult(False, f"Invalid time: {text}")
        
        return ValidationResult(True, cleaned_text=text)
    
    def _validate_url(self, text: str) -> ValidationResult:
        if not re.search(r'[a-zA-Z]+\.[a-zA-Z]+', text):
            return ValidationResult(False, f"Invalid URL: {text}")
        return ValidationResult(True, cleaned_text=text)
    
    def _validate_location(self, text: str) -> ValidationResult:
        if len(text) < 2:
            return ValidationResult(False, f"Location too short: {text}")
        return ValidationResult(True, cleaned_text=text)
    
    def _validate_user(self, text: str) -> ValidationResult:
        service_words = {"и", "с", "в", "на", "к", "от", "the", "a", "an", "with"}
        if text.lower() in service_words:
            return ValidationResult(False, f"Service word: {text}")
        return ValidationResult(True, cleaned_text=text)
    
    # ==================== ОБРАБОТКА СПИСКА СУЩНОСТЕЙ ====================
    
    def process_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Фильтрует, валидирует и очищает сущности."""
        result = []
        
        for entity in entities:
            entity_type = entity.get("entity_group", "")
            text = entity.get("word", "")
            score = entity.get("score", 0.0)
            
            validation = self.validate_entity(entity_type, text, score)
            
            if validation.is_valid:
                entity_copy = entity.copy()
                entity_copy["word"] = validation.cleaned_text or text
                entity_copy["is_valid"] = True
                result.append(entity_copy)
        
        return result
    
    def deduplicate(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        for entity in entities:
            key = (entity["entity_group"], entity["word"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique
    
    def group_by_type(self, entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {}
        for entity in entities:
            entity_type = entity.get("entity_group", "OTHER")
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(entity)
        return grouped


def format_event_for_display(event_data: Dict[str, Any]) -> str:
    lines = []
    
    title = event_data.get("title", "Событие")
    lines.append(f"📅 {title}")
    
    if event_data.get("datetime"):
        dt = datetime.fromisoformat(event_data["datetime"])
        lines.append(f"🕐 {dt.strftime('%d.%m.%Y %H:%M')}")
    elif event_data.get("date"):
        lines.append(f"📆 {event_data['date']}")
    elif event_data.get("time"):
        lines.append(f"⏰ {event_data['time']}")
    
    if event_data.get("location"):
        lines.append(f"📍 {event_data['location']}")
    
    if event_data.get("participants"):
        participants = ", ".join(event_data["participants"])
        lines.append(f"👥 {participants}")
    
    if event_data.get("url"):
        lines.append(f"🔗 {event_data['url']}")
    
    return "\n".join(lines)
