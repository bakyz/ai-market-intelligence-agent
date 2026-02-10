import json
from typing import List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    AgentRole, AgentTask, TaskStatus, GeneratedIdea,
    ResearchResult, MarketAnalysis
)
from app.llm.model_router import ModelRouter

class IdeaGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role=AgentRole.IDEA_GENERATOR,
            model=ModelRouter.get_model_for_task("synthesis")
        )

    def _get_default_system_prompt(self) -> str:
        return """You are a creative startup ideation expert with deep knowledge of:
 - Emerging technologies and trends
 - Market gaps and opportunities
 - User pain points and unmet needs
 - Successful startup patterns

 Generate innovative, feasible, and market-driven startup ideas. Focus on:
 - Solving real problems
 - Clear value propositions
 - Specific target audiences
 - Differentiated features"""

    def execute(self, task: AgentTask) -> AgentTask:
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)

            topic = task.input_data.get("topic", "")
            num_ideas = task.input_data.get("num_ideas", 3)
            research_result = task.input_data.get("research_result")
            market_analysis = task.input_data.get("market_analysis")

            context_parts = []

            if research_result and isinstance(research_result, ResearchResult):
                context_parts.append(f"""
 Research Findings:
 {research_result.summary}

 Key Insights:
 {chr(10).join(f"- {finding}" for finding in research_result.key_findings)}
 """)
            if market_analysis and isinstance(market_analysis, MarketAnalysis):
                context_parts.append(f"""
# Market Analysis:
# - Market Size: {market_analysis.market_size}
# - Maturity: {market_analysis.market_maturity}
# - Trends: {', '.join(market_analysis.trends)}
# - Opportunities: {', '.join(market_analysis.opportunities)}
# - Threats: {', '.join(market_analysis.threats)}
# """)
            context = "\n".join(context_parts) if context_parts else ""

            generation_prompt = f"""Generate {num_ideas} innovative startup ideas related to: {topic}

 {context if context else "Base ideas on general market knowledge and trends."}

 For each idea, provide JSON format:
 {{
     "title": "Short, catchy title",
     "description": "2-3 sentence description",
     "target_audience": "Specific target audience",
     "value_proposition": "Clear value proposition",
     "key_features": ["feature 1", "feature 2", "feature 3"],
     "market_opportunity": "Why this is a good opportunity",
     "inspiration_sources": ["source 1", "source 2"]
 }}

 Return as a JSON array of ideas. Make each idea:
 - Specific and actionable
 - Based on real pain points or opportunities
 - Technically feasible
 - Differentiated from existing solutions"""
            
            response = self.query_llm(generation_prompt, temperature=0.8)

            try:
                parsed = json.loads(response)
                if isinstance(parsed, dict):
                    parsed = [parsed]
            except json.JSONDecodeError:
                parsed = self._parse_ideas_fallback(response)
            
            ideas = []

            for idea_data in parsed[:num_ideas]:
                idea = GeneratedIdea(
                    title=idea_data.get("title", "Untitled Idea"),
                    description=idea_data.get("description", ""),
                    target_audience=idea_data.get("target_audience", ""),
                    value_proposition=idea_data.get("value_proposition", ""),
                    key_features=idea_data.get("key_features", []),
                    market_opportunity=idea_data.get("market_opportunity", ""),
                    inspiration_sources=idea_data.get("inspiration_sources", [])
                )
                ideas.append(idea)
            
            self._update_task_status(task, TaskStatus.COMPLETED, result=ideas)
            self.log_task(task)
        except Exception as e:
            self._update_task_status(task, TaskStatus.FAILED, error=str(e))
            self.log_task(task)

        return task
    
    def _parse_ideas_fallback(self, text: str) -> List[dict]:
        ideas = []
        lines = text.split("\n")
        current_idea = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith(("1.", "2.", "3.", "4.", "5.")) or \
               (line[0].isupper() and len(line) < 100 and ":" not in line):
                if current_idea:
                    ideas.append(current_idea)
                current_idea = {"title": line.lstrip("1234567890. ")}
            elif ":" in line and current_idea:
                key, value = line.split(":", 1)
                key = key.lower().replace(" ", "_")
                current_idea[key] = value.strip()
        
        if current_idea:
            ideas.append(current_idea)
        
        return ideas if ideas else [{"title": "Generated Idea", "description": text[:200]}] 
    
    def generate_ideas(self, topic: str, num_ideas: int = 3, research_result=None, market_analysis=None) -> List[GeneratedIdea]:
        task = self.create_task(
            "idea_generation",
            {
                "topic": topic,
                "num_ideas": num_ideas,
                "research_result": research_result,
                "market_analysis": market_analysis
            }
        )
        task = self.execute(task)
        return task.result if task.result else []
        

