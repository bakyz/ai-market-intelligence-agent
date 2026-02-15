import json
from typing import Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import AgentRole, AgentTask, TaskStatus, Critique
from app.llm.model_router import ModelRouter


class CriticAgent(BaseAgent):
    """
    Agent responsible for evaluating execution results.
    Provides critique with scores and improvement suggestions.
    """
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            role=AgentRole.CRITIC,
            model=model or ModelRouter.get_model_for_task("extraction")
        )
    
    def _get_default_system_prompt(self) -> str:
        return """You are a critical evaluator and quality assessor. Your role is to:
- Evaluate the completeness and quality of results
- Assess evidence strength and logical coherence
- Identify weaknesses and missing components
- Provide actionable improvement suggestions
- Determine if further iteration is needed

Be honest, specific, and constructive in your evaluations."""
    
    def execute(self, task: AgentTask) -> AgentTask:
        """
        Execute a critique task.
        
        Expected input_data:
            - result: Any (required) - The result to evaluate
            - goal: str (required) - The original goal
            - context: str (optional) - Additional context
        """
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
            result = task.input_data.get("result")
            goal = task.input_data.get("goal", "")
            context = task.input_data.get("context", "")
            
            if result is None:
                raise ValueError("Critique task requires 'result' in input_data")
            
            # Evaluate the result
            critique = self.evaluate(result, goal, context)
            
            self._update_task_status(task, TaskStatus.COMPLETED, result=critique)
            self.log_task(task)
            
        except Exception as e:
            self._update_task_status(task, TaskStatus.FAILED, error=str(e))
            self.log_task(task)
        
        return task
    
    def evaluate(
        self,
        result: Any,
        goal: str,
        context: str = ""
    ) -> Critique:
        """
        Evaluate a result and provide critique.
        
        Args:
            result: The result to evaluate
            goal: The original goal
            context: Additional context
            
        Returns:
            Critique object with scores and feedback
        """
        # Format result for evaluation
        result_text = self._format_result(result)
        
        evaluation_prompt = f"""Evaluate this research/analysis result against the original goal.

Goal: {goal}

{context if context else ""}

Result to Evaluate:
{result_text}

Provide a comprehensive evaluation in JSON format:
{{
    "completeness_score": 0.0-1.0,  // Did we fully answer the goal?
    "evidence_strength_score": 0.0-1.0,  // How strong is the supporting evidence?
    "coherence_score": 0.0-1.0,  // Is the logic sound and coherent?
    "actionability_score": 0.0-1.0,  // How actionable are the findings?
    "overall_score": 0.0-1.0,  // Overall quality score
    "weaknesses": ["weakness 1", "weakness 2"],
    "missing_components": ["missing 1", "missing 2"],
    "improvement_suggestions": ["suggestion 1", "suggestion 2"],
    "should_iterate": true/false,  // Should we refine and iterate?
    "confidence": 0.0-1.0  // Confidence in this evaluation
}}

Scoring Guidelines:
- Completeness: Does the result fully address the goal? Are key questions answered?
- Evidence Strength: Are claims supported by data/evidence? Is the research thorough?
- Coherence: Is the reasoning logical? Are conclusions well-supported?
- Actionability: Can the findings be acted upon? Are recommendations clear?
- Overall: Weighted average (completeness 0.3, evidence 0.3, coherence 0.2, actionability 0.2)

Be specific and honest. If the result is incomplete or weak, clearly state what's missing."""

        response = self.query_llm(
            evaluation_prompt,
            temperature=0.3  # Lower temperature for more deterministic critique
        )
        
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            parsed = self._parse_fallback(response)
        
        # Calculate overall score if not provided
        overall_score = parsed.get("overall_score")
        if overall_score is None:
            overall_score = (
                parsed.get("completeness_score", 0.5) * 0.3 +
                parsed.get("evidence_strength_score", 0.5) * 0.3 +
                parsed.get("coherence_score", 0.5) * 0.2 +
                parsed.get("actionability_score", 0.5) * 0.2
            )
        
        critique = Critique(
            completeness_score=float(parsed.get("completeness_score", 0.5)),
            evidence_strength_score=float(parsed.get("evidence_strength_score", 0.5)),
            coherence_score=float(parsed.get("coherence_score", 0.5)),
            actionability_score=float(parsed.get("actionability_score", 0.5)),
            overall_score=float(overall_score),
            weaknesses=parsed.get("weaknesses", []),
            missing_components=parsed.get("missing_components", []),
            improvement_suggestions=parsed.get("improvement_suggestions", []),
            should_iterate=parsed.get("should_iterate", True),
            confidence=float(parsed.get("confidence", 0.7)),
            timestamp=datetime.now()
        )
        
        return critique
    
    def _format_result(self, result: Any) -> str:
        """Format result for evaluation"""
        if hasattr(result, 'summary'):
            return f"Summary: {result.summary}\n\nDetails: {str(result)}"
        elif hasattr(result, '__dict__'):
            # Try to extract meaningful fields
            parts = []
            for key, value in result.__dict__.items():
                if not key.startswith('_'):
                    parts.append(f"{key}: {value}")
            return "\n".join(parts)
        else:
            return str(result)[:2000]  # Truncate very long results
    
    def _parse_fallback(self, text: str) -> dict:
        """Fallback parser if JSON parsing fails"""
        return {
            "completeness_score": 0.5,
            "evidence_strength_score": 0.5,
            "coherence_score": 0.5,
            "actionability_score": 0.5,
            "overall_score": 0.5,
            "weaknesses": ["Unable to parse evaluation"],
            "missing_components": [],
            "improvement_suggestions": ["Improve result formatting"],
            "should_iterate": True,
            "confidence": 0.3
        }

