# app/vector_db/chroma_client.py

import chromadb
from chromadb.utils import embedding_functions


class ChromaVectorDB:
    def __init__(self, config):
        # Support both AppSettings and VectorDBConfig
        if hasattr(config, "vectordb"):
            config = config.vectordb

        self.config = config

        self.client = chromadb.PersistentClient(
            path=config.persist_directory
        )

        self.collection = self.client.get_or_create_collection(
            name=config.collection_name
        )


    def add_documents(self, ids, documents, embeddings=None, metadatas=None):
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(self, query_embeddings, n_results=5):
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results
        )

    def count(self):
        return self.collection.count()




