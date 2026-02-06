import hashlib
import json
from app.config.settings import get_settings

settings = get_settings()

class CacheManager:
    def __init__(self):
        self.cache = {}

    def _generate_key(self, model: str, messages: list) -> str:
        data = f"{model}:{json.dumps(messages, sort_keys=True)}"
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, model: str, messages: list):
        key = self._generate_key(model, messages)
        return self.cache.get(key)

    def set(self, model: str, messages: list, response: str):
        key = self._generate_key(model, messages)
        if settings.cache.ENABLE_CACHE:
            self.cache[key] = response
