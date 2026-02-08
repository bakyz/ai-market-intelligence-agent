from collections import Counter
from typing import List
from app.rag.schemas import RetrievedDocument


class TrendDetector:
    def detect(self, docs: List[RetrievedDocument], top_k=5):

        words = []

        for d in docs:
            words.extend(d.text.split())

        counter = Counter(words)

        return counter.most_common(top_k)
