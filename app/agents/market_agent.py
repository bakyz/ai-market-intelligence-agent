import json
from typing import List, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import AgentRole, AgentTask, TaskStatus, MarketAnalysis, ResearchResult
from app.llm.model_router import ModelRouter


# class MarketAgent(BaseAgent):
    
#     def __init__(self):
#         super().__init__(
#             role=AgentRole.MARKET_ANALYST,
#             model=ModelRouter.get_model_for_task("extraction")
#         )
    
#     def _get_default_system_prompt(self) -> str:
#         return """You are a senior market analyst with expertise in startup ecosystems, 
# technology markets, and emerging trends. Your role is to:
# - Analyze market dynamics and trends
# - Assess market size and growth potential
# - Identify opportunities and threats
# - Evaluate competitive landscapes
# - Determine market maturity stages
# Provide data-driven, objective analysis."""
    
#     def execute(self, task: AgentTask) -> AgentTask:
#         """Execute a market analysis task"""
#         try:
#             self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
#             topic = task.input_data.get("topic", "")
#             research_result = task.input_data.get("research_result")
            
#             context = ""
#             if research_result and isinstance(research_result, ResearchResult):
#                 context = f"""
# Research Summary:
# {research_result.summary}

# Key Findings:
# {chr(10).join(f"- {finding}" for finding in research_result.key_findings)}

# Sources: {', '.join(research_result.sources)}
# """
            
#             analysis_prompt = f"""Analyze the market for: {topic}

# {context if context else "No prior research provided. Base your analysis on general market knowledge."}

# Provide a comprehensive market analysis in JSON format:
# {{
#     "market_size": "Estimated market size (e.g., '$X billion', 'growing rapidly', 'unknown')",
#     "trends": ["trend 1", "trend 2", "trend 3"],
#     "opportunities": ["opportunity 1", "opportunity 2"],
#     "threats": ["threat 1", "threat 2"],
#     "competitive_landscape": "Description of competition and market structure",
#     "market_maturity": "emerging|growing|mature|declining",
#     "confidence_score": 0.0-1.0
# }}

# Be specific and data-driven where possible."""
            
#             response = self.query_llm(analysis_prompt)
            
#             try:
#                 parsed = json.loads(response)
#             except json.JSONDecodeError:
#                 parsed = self._parse_market_analysis_fallback(response)
            
#             result = MarketAnalysis(
#                 topic=topic,
#                 market_size=parsed.get("market_size"),
#                 trends=parsed.get("trends", []),
#                 opportunities=parsed.get("opportunities", []),
#                 threats=parsed.get("threats", []),
#                 competitive_landscape=parsed.get("competitive_landscape", ""),
#                 market_maturity=parsed.get("market_maturity", "unknown"),
#                 confidence_score=float(parsed.get("confidence_score", 0.5))
#             )
            
#             self._update_task_status(task, TaskStatus.COMPLETED, result=result)
#             self.log_task(task)
            
#         except Exception as e:
#             self._update_task_status(
#                 task,
#                 TaskStatus.FAILED,
#                 error=str(e)
#             )
#             self.log_task(task)
        
#         return task
    
#     def _parse_market_analysis_fallback(self, text: str) -> dict:
#         """Fallback parser if JSON parsing fails"""
#         return {
#             "market_size": "Unknown",
#             "trends": [],
#             "opportunities": [],
#             "threats": [],
#             "competitive_landscape": text[:500],
#             "market_maturity": "unknown",
#             "confidence_score": 0.5
#         }
    
#     def analyze_market(
#         self,
#         topic: str,
#         research_result: Optional[ResearchResult] = None
#     ) -> MarketAnalysis:
#         """Convenience method for quick market analysis"""
#         task = self.create_task(
#             "market_analysis",
#             {
#                 "topic": topic,
#                 "research_result": research_result
#             }
#         )
#         task = self.execute(task)
#         return task.result

class MarketAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role = AgentRole.MARKET_ANALYST,
            model = ModelRouter.get_model_for_task("extraction")
        )
    
    def _get_default_system_prompt(self) -> str:
        return """You are a senior market analyst with expertise in startup ecosystems, 
 technology markets, and emerging trends. Your role is to:
 - Analyze market dynamics and trends
 - Assess market size and growth potential
 - Identify opportunities and threats
 - Evaluate competitive landscapes
 - Determine market maturity stages
 Provide data-driven, objective analysis."""
    
    def execute(self, task: AgentTask) -> AgentTask:
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)

            topic = task.input_data.get("topic", "")
            research_result = task.input_data.get("research_result")

            if research_result and isinstance(research_result, ResearchResult):
                context = f"""
 Research Summary: {research_result.summary}

 Key Findings:
 {chr(10).join(f"- {finding}" for finding in research_result.key_findings)}

 Sources: {', '.join(research_result.sources)}
 """
            analysis_prompt = f"""Analyze the market for: {topic}

 {context if context else "No prior research provided. Base your analysis on general market knowledge."}

 Provide a comprehensive market analysis in JSON format:
 {{
     "market_size": "Estimated market size (e.g., '$X billion', 'growing rapidly', 'unknown')",
     "trends": ["trend 1", "trend 2", "trend 3"],
     "opportunities": ["opportunity 1", "opportunity 2"],
     "threats": ["threat 1", "threat 2"],
     "competitive_landscape": "Description of competition and market structure",
     "market_maturity": "emerging|growing|mature|declining",
     "confidence_score": 0.0-1.0
 }}

 Be specific and data-driven where possible.""" 
            
            response = self.query_llm(analysis_prompt)

            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                parsed = self._parse_market_analysis_fallback(response)
            
            result = MarketAnalysis(
                topic=topic,
                market_size=parsed.get("market_size"),
                trends=parsed.get("trends", []),
                opportunities=parsed.get("opportunities", []),
                threats=parsed.get("threats", []),
                competitive_landscape=parsed.get("competitive_landscape", ""),
                market_maturity=parsed.get("market_maturity", "unknown"),
                confidence_score=float(parsed.get("confidence_score", 0.5))
            )

            self._update_task_status(task, TaskStatus.COMPLETED, result=result)
            self.log_task(task)
        except Exception as e:
            self._update_task_status(
                task,
                TaskStatus.FAILED,
                error=str(e)
            )
            self.log_task(task)
        return task

    def _parse_market_analysis_fallback(self, text: str) -> dict:
        return {
            "market_size": "Unknown",
            "trends": [],
            "opportunities": [],
            "threats": [],
            "competitive_landscape": text[:500],
            "market_maturity": "unknown",
            "confidence_score": 0.5
        }
    
    def analyze_market(
        self,
        topic: str,
        research_result: Optional[ResearchResult] = None
    ) -> MarketAnalysis:
        task = self.create_task(
            "market_analysis",
            {
                "topic": topic,
                "research_result": research_result
            }
        )
        task = self.execute(task)
        return task.result