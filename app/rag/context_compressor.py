from typing import List
from app.rag.schemas import RetrievedDocument


class ContextCompressor:
    def __init__(self, max_chars: int = 8000):
        self.max_chars = max_chars

    def compress(self, docs: List[RetrievedDocument]) -> str:
        context = ""

        for doc in docs:
            chunk = f"[Source:{doc.metadata.get('source')}]\n{doc.text}\n\n"

            if len(context) + len(chunk) > self.max_chars:
                break

            context += chunk

        return context.strip()
