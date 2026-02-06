from app.config.settings import get_settings
from app.llm.cache_manager import CacheManager
from app.llm.retry_handler import retry_with_backoff
from app.llm.model_router import ModelRouter

settings = get_settings()

class LLMWrapper:
    def __init__(self, model: str = None):
        self.model = model or settings.model.model_routing.IDEATION_MODEL
        self.cache = CacheManager()
    
    @retry_with_backoff(retries=settings.llm.MAX_RETRIES, backpff_in_seconds=1)

    def query(self, prompt: str, system_prompt="You are a helpful assistant"):
        cached = self.cache.get(self.model, [{"role": "user", "content": prompt}])
        if cached:
            return cached
        
        import openai
        openai.api_key = settings.OPENAI_API_KEY

        response = openai.ChatCompletion.Create(
            model = self.model,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature = settings.model.TEMPERATURE,
            max_tokens = settings.model.MAX_TOKENS
        )

        answer = response.choices[0].message.content
        self.cache.set(self.model, [{"role": "user", "content": prompt}], answer)
        return answer