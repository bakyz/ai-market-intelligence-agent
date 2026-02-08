import json
from tqdm import tqdm

from app.vector_db.schemas import Document
from app.vector_db.deduplicator import hash_text
from app.vector_db.embedding_service import EmbeddingService
from app.vector_db.cache import EmbeddingCache
from app.vector_db.chroma_client import ChromaVectorDB
from app.vector_db.logger import get_logger
from app.vector_db.config import VectorDBConfig


logger = get_logger("ingestion_pipeline")


class VectorIngestionPipeline:
    def __init__(self, config: VectorDBConfig):
        self.config = config
        self.db = ChromaVectorDB(config)
        self.embedder = EmbeddingService(
            model=config.embedding_model,
            max_retries=config.max_retries,
        )
        self.cache = EmbeddingCache()

    def load_json(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []

        for item in data:
            text = f"{item.get('title','')} {item.get('body','')}".strip()

            doc = Document(
                id=hash_text(text),
                text=text,
                metadata={
                    "source": item.get("source"),
                    "score": item.get("score"),
                    "comments": item.get("comments"),
                    "created_at": item.get("created_at"),
                },
            )
            documents.append(doc)

        return documents

    def index(self, documents):
        batch_size = self.config.batch_size

        for i in tqdm(range(0, len(documents), batch_size)):
            batch = documents[i : i + batch_size]

            texts = []
            ids = []
            metas = []
            embeddings = []

            for doc in batch:
                cached = self.cache.get(doc.id)

                if cached:
                    embeddings.append(cached)
                else:
                    texts.append(doc.text)

                ids.append(doc.id)
                metas.append(doc.metadata)

            if texts:
                new_embeddings = self.embedder.embed_batch(texts)

                for text, emb in zip(texts, new_embeddings):
                    self.cache.set(hash_text(text), emb)
                    embeddings.append(emb)

            self.db.add_documents(
                ids=ids,
                embeddings=embeddings,
                documents=[d.text for d in batch],
                metadatas=metas,
            )

            logger.info(f"Indexed batch size={len(batch)}")
