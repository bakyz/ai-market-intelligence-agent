import json
from pathlib import Path


class EmbeddingCache:
    def __init__(self, path="data/cache/embeddings.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if self.path.exists():
            self.cache = json.loads(self.path.read_text())
        else:
            self.cache = {}

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value
        self.path.write_text(json.dumps(self.cache))
