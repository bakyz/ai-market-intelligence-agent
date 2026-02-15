import time
from openai import OpenAI
from app.vector_db.logger import get_logger
from app.config.settings import get_settings

settings = get_settings()
logger = get_logger("embedding_service")


class EmbeddingService:
    def __init__(self, model: str, max_retries=3):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.max_retries = max_retries

    def embed_batch(self, texts):
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                )
                return [e.embedding for e in response.data]

            except Exception as e:
                wait = 2 ** attempt
                logger.warning(f"Embedding failed, retrying in {wait}s | {e}")
                time.sleep(wait)

        raise RuntimeError("Embedding failed after retries")
    
    def embed(self, text):
        """Embed a single string."""
        return self.embed_batch([text])[0]
