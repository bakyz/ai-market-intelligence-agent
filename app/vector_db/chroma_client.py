import chromadb
from chromadb.config import Settings
from app.vector_db.config import VectorDBConfig


class ChromaVectorDB:
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.config.persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(name=self.config.collection_name)
    
    def add_documents(self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None):
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def query(self, query_embedding, top_k=5):
        return self.collection_query(query_embedding=query_embedding, n_results=top_k)
    