from app.config.settings import get_settings

settings = get_settings()

class ModelRouter:
    MODEL_MAP = {
        "synthesis": settings.model.model_routing.IDEATION_MODEL,
        "extraction": settings.model.model_routing.ANALYSIS_MODEL,
        "classification": settings.model.model_routing.CLASSIFICATION_MODEL
        if hasattr(settings.model.model_routing, "CLASSIFICATION_MODEL")
        else settings.model.model_routing.ANALYSIS_MODEL
    }

    @classmethod
    def get_model_for_task(cls, task_type: str):
        return cls.MODEL_MAP.get(task_type, settings.model.model_routing.IDEATION_MODEL)
