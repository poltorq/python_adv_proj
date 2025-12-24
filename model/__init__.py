"""
Model Package — NER модель для извлечения событий из текста.

Использование:
    from model import process_text, extract_event
    
    event = process_text("Встреча завтра в 15:00")
    print(event.to_json())
    
    data = extract_event("Созвон с командой в понедельник")
    print(data)
"""

from .dataclasses import (
    NEREntity,
    EventSlots,
    EventData,
    ParsedDateTime,
    EntityType,
)

from .postprocessing import (
    NERPostprocessor,
    PostprocessorConfig,
    ValidationResult,
    format_event_for_display,
)

from .parser import (
    DateTimeParser,
    ParserConfig,
    parse_date,
    parse_time,
    parse_datetime,
)

from .evaluator import (
    NERModel,
    EvaluatorConfig,
    get_model,
    predict,
)

from .pipeline import (
    NERPipeline,
    PipelineConfig,
    get_pipeline,
    process_text,
    extract_event,
)

__all__ = [
    "NEREntity",
    "EventSlots", 
    "EventData",
    "ParsedDateTime",
    "EntityType",
    "NERPostprocessor",
    "PostprocessorConfig",
    "ValidationResult",
    "format_event_for_display",
    "DateTimeParser",
    "ParserConfig",
    "parse_date",
    "parse_time",
    "parse_datetime",
    "NERModel",
    "EvaluatorConfig",
    "get_model",
    "predict",
    "NERPipeline",
    "PipelineConfig",
    "get_pipeline",
    "process_text",
    "extract_event",
]
