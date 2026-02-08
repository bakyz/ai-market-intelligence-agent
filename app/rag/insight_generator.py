from app.llm.client import LLMWrapper
from app.llm.model_router import ModelRouter
from app.rag.schemas import InsightResult
import json


class InsightGenerator:
    def __init__(self):
        model = ModelRouter.get_model_for_task("synthesis")
        self.llm = LLMWrapper(model=model)

    def generate(self, query: str, context: str) -> InsightResult:

        system_prompt = """
You are a senior startup analyst.
Extract:
- key pain points
- market opportunities
- emerging trends
- strong signals
Return JSON.
"""

        prompt = f"""
QUERY:
{query}

DATA:
{context}

OUTPUT FORMAT:
{{
 "summary": "",
 "pain_points": [],
 "opportunities": [],
 "signals": []
}}
"""

        response = self.llm.query(prompt, system_prompt=system_prompt)

        data = json.loads(response)

        return InsightResult(
            summary=data.get("summary", ""),
            pain_points=data.get("pain_points", []),
            opportunities=data.get("opportunities", []),
            signals=data.get("signals", []),
        )
