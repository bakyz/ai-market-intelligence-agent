from app.config.settings import get_settings

settings = get_settings()

class ModelRouter:
    MODEL_MAP = {
        "synthesis": settings.model_routing.IDEATION_MODEL,
        "extraction": settings.model_routing.ANALYSIS_MODEL,
        "classification": settings.model_routing.CLASSIFICATION_MODEL
        if hasattr(settings.model_routing, "CLASSIFICATION_MODEL")
        else settings.model_routing.ANALYSIS_MODEL
    }

    @classmethod
    def get_model_for_task(cls, task_type: str):
        return cls.MODEL_MAP.get(task_type, settings.model_routing.IDEATION_MODEL)
