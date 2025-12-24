import os
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

warnings.filterwarnings("ignore", message=".*incorrect regex pattern.*")


@dataclass
class EvaluatorConfig:
    model_path: str = field(default_factory=lambda: str(
        Path(__file__).parent / "trained_model"
    ))
    aggregation_strategy: str = "simple"
    device: int = -1
    use_gpu_if_available: bool = True


class NERModel:
    """Обёртка над HuggingFace NER pipeline."""
    
    def __init__(self, config: Optional[EvaluatorConfig] = None):
        self.config = config or EvaluatorConfig()
        self._pipeline = None
        self._is_loaded = False
    
    def _get_device(self) -> int:
        if not self.config.use_gpu_if_available:
            return -1
        
        try:
            import torch
            if torch.cuda.is_available():
                return 0
        except ImportError:
            pass
        
        return self.config.device
    
    def load(self) -> "NERModel":
        if self._is_loaded:
            return self
        
        from transformers import pipeline
        
        model_path = self.config.model_path
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                "Please train the model first or provide correct path."
            )
        
        self._pipeline = pipeline(
            "ner",
            model=model_path,
            tokenizer=model_path,
            aggregation_strategy=self.config.aggregation_strategy,
            device=self._get_device(),
        )
        
        self._is_loaded = True
        return self
    
    def predict(self, text: str) -> List[Dict[str, Any]]:
        if not self._is_loaded:
            self.load()
        
        results = self._pipeline(text)
        
        entities = []
        for r in results:
            entities.append({
                "entity_group": r.get("entity_group", r.get("entity", "")),
                "word": r.get("word", ""),
                "score": float(r.get("score", 0.0)),
                "start": int(r.get("start", 0)),
                "end": int(r.get("end", 0)),
            })
        
        return entities
    
    def __call__(self, text: str) -> List[Dict[str, Any]]:
        return self.predict(text)


_global_model: Optional[NERModel] = None


def get_model(config: Optional[EvaluatorConfig] = None) -> NERModel:
    global _global_model
    if _global_model is None:
        _global_model = NERModel(config)
        _global_model.load()
    return _global_model


def predict(text: str) -> List[Dict[str, Any]]:
    return get_model().predict(text)
