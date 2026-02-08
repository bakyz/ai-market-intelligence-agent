from openai import OpenAI
from app.vector_db.chroma_client import ChromaVectorDB
from app.vector_db.config import VectorDBConfig
from app.config.settings import get_settings

settings = get_settings()


class SemanticSearchEngine:
    def __init__(self, config: VectorDBConfig):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = config.embedding_model
        self.db = ChromaVectorDB(config)

    def embed_query(self, query):
        response = self.client.embeddings.create(
            model=self.model,
            input=[query],
        )
        return response.data[0].embedding

    def search(self, query, top_k=5):
        embedding = self.embed_query(query)
        return self.db.query(embedding, top_k)
