from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .dataclasses import (
    NEREntity, 
    EventSlots, 
    EventData,
    ParsedDateTime,
)
from .postprocessing import NERPostprocessor, PostprocessorConfig
from .parser import DateTimeParser, ParserConfig
from .evaluator import NERModel, EvaluatorConfig


@dataclass
class PipelineConfig:
    evaluator_config: Optional[EvaluatorConfig] = None
    postprocessor_config: Optional[PostprocessorConfig] = None
    parser_config: Optional[ParserConfig] = None
    min_entity_score: float = 0.5
    require_datetime: bool = False


class NERPipeline:
    """
    Полный пайплайн обработки NER.
    
    Использование:
        pipeline = NERPipeline()
        event = pipeline.process("Встреча завтра в 15:00 в офисе")
        json_data = event.to_backend_format()
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.model = NERModel(self.config.evaluator_config)
        self.postprocessor = NERPostprocessor(self.config.postprocessor_config)
        self.parser = DateTimeParser(self.config.parser_config)
    
    def load_model(self) -> "NERPipeline":
        self.model.load()
        return self
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        return self.model.predict(text)
    
    def validate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.postprocessor.process_entities(entities)
    
    def parse_datetime_entities(
        self, 
        entities: List[Dict[str, Any]],
        reference_date: Optional[datetime] = None
    ) -> Dict[str, List[ParsedDateTime]]:
        if reference_date:
            self.parser.reference_date = reference_date
        
        result = {"dates": [], "times": []}
        
        for entity in entities:
            entity_type = entity.get("entity_group", "")
            text = entity.get("word", "")
            
            if entity_type == "DATE":
                parsed_date = self.parser.parse_date(text)
                if parsed_date:
                    result["dates"].append(ParsedDateTime(
                        date_value=parsed_date,
                        original_text=text,
                        is_relative=text.lower() in self.parser.config.relative_dates_ru
                    ))
            
            elif entity_type == "TIME":
                parsed_time = self.parser.parse_time(text)
                if parsed_time:
                    result["times"].append(ParsedDateTime(
                        time_value=parsed_time,
                        original_text=text
                    ))
        
        return result
    
    def build_slots(
        self, 
        entities: List[Dict[str, Any]],
        parsed_datetime: Dict[str, List[ParsedDateTime]]
    ) -> EventSlots:
        slots = EventSlots()
        
        for entity in entities:
            entity_type = entity.get("entity_group", "")
            text = entity.get("word", "")
            
            if entity_type == "TITLE" and not slots.event_name:
                slots.event_name = text
            elif entity_type == "DATE" and not slots.date_raw:
                slots.date_raw = text
            elif entity_type == "TIME" and not slots.time_raw:
                slots.time_raw = text
            elif entity_type == "LOC" and not slots.location:
                slots.location = text
            elif entity_type == "USER":
                if text not in slots.participants:
                    slots.participants.append(text)
            elif entity_type == "URL" and not slots.url:
                slots.url = text
        
        if parsed_datetime["dates"]:
            slots.date_parsed = parsed_datetime["dates"][0].date_value
        
        if parsed_datetime["times"]:
            slots.time_parsed = parsed_datetime["times"][0].time_value
        
        return slots
    
    def build_event(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        slots: EventSlots
    ) -> EventData:
        ner_entities = [
            NEREntity(
                entity_type=e.get("entity_group", ""),
                text=e.get("word", ""),
                score=e.get("score", 0.0),
                start=e.get("start", 0),
                end=e.get("end", 0),
                is_valid=e.get("is_valid", True)
            )
            for e in entities
        ]
        
        is_valid = True
        validation_errors = []
        
        if self.config.require_datetime:
            if not slots.date_parsed and not slots.time_parsed:
                is_valid = False
                validation_errors.append("No date or time found")
        
        return EventData(
            original_text=text,
            slots=slots,
            raw_entities=ner_entities,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )
    
    def process(self, text: str, reference_date: Optional[datetime] = None) -> EventData:
        raw_entities = self.extract_entities(text)
        valid_entities = self.validate_entities(raw_entities)
        parsed_dt = self.parse_datetime_entities(valid_entities, reference_date)
        slots = self.build_slots(valid_entities, parsed_dt)
        return self.build_event(text, valid_entities, slots)
    
    def to_json(self, text: str, reference_date: Optional[datetime] = None, **kwargs) -> str:
        return self.process(text, reference_date).to_json(**kwargs)
    
    def to_backend_format(self, text: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
        return self.process(text, reference_date).to_backend_format()


_global_pipeline: Optional[NERPipeline] = None


def get_pipeline(config: Optional[PipelineConfig] = None) -> NERPipeline:
    global _global_pipeline
    if _global_pipeline is None:
        _global_pipeline = NERPipeline(config)
        _global_pipeline.load_model()
    return _global_pipeline


def process_text(text: str, reference_date: Optional[datetime] = None) -> EventData:
    return get_pipeline().process(text, reference_date)


def extract_event(text: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
    return get_pipeline().to_backend_format(text, reference_date)
