import json
from typing import List
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import (
    AgentRole, AgentTask, TaskStatus, IdeaEvaluation, 
    GeneratedIdea, MarketAnalysis
)
from app.llm.model_router import ModelRouter


class EvaluatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role=AgentRole.EVALUATOR,
            model=ModelRouter.get_model_for_task("extraction")
        )

    def _get_default_system_prompt(self) -> str:
        return """You are a senior startup evaluator and advisor with experience in:
# - Product-market fit assessment
# - Market opportunity evaluation
# - Feasibility analysis
# - Risk assessment
# - Investment decision-making

# Provide honest, critical, and constructive evaluations. Be specific about strengths, 
# weaknesses, and actionable recommendations."""


    def execute(self, task: AgentTask) -> AgentTask:
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)
            idea = task.input_data.get("idea")
            idea_obj = task.input_data.get("idea_obj")
            market_analysis = task.input_data.get("market_analysis")

            if idea_obj and isinstance(idea_obj, GeneratedIdea):
                idea_text = f"""
                Title: {idea_obj.title}
Description: {idea_obj.description}
Target Audience: {idea_obj.target_audience}
Value Proposition: {idea_obj.value_proposition}
Key Features: {', '.join(idea_obj.key_features)}
Market Opportunity: {idea_obj.market_opportunity}"""
            else:
                idea_text = idea or "No idea provided"

            market_context = ""
            if market_analysis and isinstance(market_analysis, MarketAnalysis):
                market_context = f"""
                 Market Context:
 - Market Size: {market_analysis.market_size}
 - Market Maturity: {market_analysis.market_maturity}
 - Trends: {', '.join(market_analysis.trends)}
 - Opportunities: {', '.join(market_analysis.opportunities)}
 - Threats: {', '.join(market_analysis.threats)}
 - Competitive Landscape: {market_analysis.competitive_landscape}"""
    
            evaluation_prompt = f"""Evaluate the following startup idea:

 {idea_text}

 {market_context if market_context else ""}

 Provide a comprehensive evaluation in JSON format:
 {{
     "feasibility_score": 0.0-1.0,
     "market_potential_score": 0.0-1.0,
     "innovation_score": 0.0-1.0,
     "overall_score": 0.0-1.0,
     "strengths": ["strength 1", "strength 2"],
     "weaknesses": ["weakness 1", "weakness 2"],
     "risks": ["risk 1", "risk 2"],
     "recommendations": ["recommendation 1", "recommendation 2"],
     "verdict": "high_potential|medium_potential|low_potential"
 }}

 Scoring guidelines:
 - Feasibility: Can this be built? (technical, resource, time constraints)
 - Market Potential: Is there a real market need? (size, growth, willingness to pay)
 - Innovation: How novel/unique is this? (differentiation, competitive advantage)
 - Overall: Weighted average considering all factors

 Be honest and specific."""

            response = self.query_llm(evaluation_prompt)

            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                parsed = self._parse_evaluation_fallback(response)
            
            overall_score = parsed.get("overall_score")
            if overall_score is None:
                overall_score = (
                    parsed.get("feasibility_score", 0.5) * 0.3 +
                    parsed.get("market_potential_score", 0.5) * 0.4 +
                    parsed.get("innovation_score", 0.5) * 0.3
                )
            
            result = IdeaEvaluation(
                idea=idea_text,
                feasibility_score=float(parsed.get("feasibility_score", 0.5)),
                market_potential_score=float(parsed.get("market_potential_score", 0.5)),
                innovation_score=float(parsed.get("innovation_score", 0.5)),
                overall_score=float(overall_score),
                strengths=parsed.get("strengths", []),
                weaknesses=parsed.get("weaknesses", []),
                risks=parsed.get("risks", []),
                recommendations=parsed.get("recommendations", []),
                verdict=parsed.get("verdict", "medium_potential")
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
    
    def _parse_evaluation_fallback(self, text: str) -> dict:
        return {
            "feasibility_score": 0.5,
            "market_potential_score": 0.5,
            "innovation_score": 0.5,
            "overall_score": 0.5,
            "strengths": [],
            "weaknesses": [],
            "risks": [],
            "recommendations": [],
            "verdict": "medium_potential"
        }
    
    def evaluate_idea(self, idea: str = None, idea_obj: GeneratedIdea = None, market_analysis: MarketAnalysis = None) -> IdeaEvaluation:
        task = self.create_task(
            "idea_evaluation",
            {
                "idea": idea,
                "idea_obj": idea_obj,
                "market_analysis": market_analysis
            }
        )
        result_task = self.execute(task)
        return result_task.result
