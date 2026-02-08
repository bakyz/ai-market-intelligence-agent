from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class RetrievedDocument:
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float


@dataclass
class InsightResult:
    summary: str
    pain_points: List[str]
    opportunities: List[str]
    signals: List[str]
