"""Model loader for managing ML artifacts and versioned models."""

import os
from pathlib import Path
from typing import Any
import joblib

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger("model_loader")


class ModelLoader:
    _models: dict[str, Any] = {}

    @classmethod
    def get_models_dir(cls) -> Path:
        base_dir = Path(settings.ML_MODELS_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    @classmethod
    def load_model(cls, model_name: str, version: str) -> Any | None:
        cache_key = f"{model_name}_{version}"
        if cache_key in cls._models:
            return cls._models[cache_key]

        model_path = cls.get_models_dir() / f"{model_name}_{version}.joblib"
        if model_path.exists():
            try:
                model = joblib.load(model_path)
                cls._models[cache_key] = model
                logger.info(f"Loaded ML model: {model_path}")
                return model
            except Exception as e:
                logger.error(f"Failed loading model {model_path}: {e}")
                return None
        else:
            logger.info(f"Model file {model_path} not found on disk. Using built-in statistical model.")
            return None

    @classmethod
    def save_model(cls, model: Any, model_name: str, version: str) -> Path:
        model_path = cls.get_models_dir() / f"{model_name}_{version}.joblib"
        joblib.dump(model, model_path)
        cache_key = f"{model_name}_{version}"
        cls._models[cache_key] = model
        logger.info(f"Saved ML model: {model_path}")
        return model_path
