from openai import OpenAI
from app.vector_db.chroma_client import ChromaVectorDB
from app.vector_db.config import VectorDBConfig


class SemanticSearchEngine:
    def __init__(self, config: VectorDBConfig):
        self.client = OpenAI()
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
