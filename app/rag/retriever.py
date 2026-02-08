from typing import List
from app.vector_db.semantic_search import SemanticSearchEngine
from app.vector_db.config import VectorDBConfig
from app.rag.schemas import RetrievedDocument


class RAGRetriever:
    def __init__(self, config: VectorDBConfig):
        self.engine = SemanticSearchEngine(config)

    def retrieve(self, query: str, top_k: int = 10) -> List[RetrievedDocument]:
        results = self.engine.search(query, top_k=top_k)

        docs = []

        ids = results["ids"][0]
        texts = results["documents"][0]
        metas = results["metadatas"][0]
        scores = results["distances"][0]

        for i in range(len(ids)):
            docs.append(
                RetrievedDocument(
                    id=ids[i],
                    text=texts[i],
                    metadata=metas[i],
                    score=scores[i],
                )
            )

        return docs
