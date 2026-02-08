from dataclasses import dataclass

@dataclass
class VectorDBConfig:
    persist_directory: str = "data/vector_db"
    collection_name: str = "startup_ideas"
    embedding_model: str = "text-embedding-3-small"
    batch_size: int = 32
    max_retries: int = 3
    
