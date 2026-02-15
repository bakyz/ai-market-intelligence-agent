from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import AgentRole, AgentTask, TaskStatus, Plan
from app.planning.planning_engine import PlanningEngine
from app.llm.model_router import ModelRouter


class PlannerAgent(BaseAgent):
    """Agent responsible for creating execution plans from high-level goals"""
    
    def __init__(self, model: Optional[str] = None):
        super().__init__(
            role=AgentRole.PLANNER,
            model=model or ModelRouter.get_model_for_task("synthesis")
        )
        self.planning_engine = PlanningEngine(model=self.model)
    
    def _get_default_system_prompt(self) -> str:
        return """You are an expert strategic planner specializing in breaking down complex goals 
into actionable, structured execution plans. You understand:
- Task dependencies and sequencing
- Resource allocation
- Risk assessment
- Iterative refinement

Create clear, logical plans that can be executed step-by-step."""
    
    def execute(self, task: AgentTask) -> AgentTask:
        """
        Execute a planning task.
        
        Expected input_data:
            - goal: str (required)
            - context: Dict[str, Any] (optional)
            - plan_id: str (optional)
            - version: int (optional, default 1)
        """
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
            goal = task.input_data.get("goal")
            if not goal:
                raise ValueError("Planning task requires 'goal' in input_data")
            
            context = task.input_data.get("context")
            plan_id = task.input_data.get("plan_id")
            version = task.input_data.get("version", 1)
            
            # Create plan
            plan = self.planning_engine.create_plan(
                goal=goal,
                context=context,
                plan_id=plan_id,
                version=version
            )
            
            # Validate plan
            is_valid, issues = self.planning_engine.validate_plan(plan)
            if not is_valid:
                raise ValueError(f"Generated plan is invalid: {', '.join(issues)}")
            
            self._update_task_status(task, TaskStatus.COMPLETED, result=plan)
            self.log_task(task)
            
        except Exception as e:
            self._update_task_status(task, TaskStatus.FAILED, error=str(e))
            self.log_task(task)
        
        return task
    
    def create_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """
        Convenience method to create a plan.
        
        Args:
            goal: High-level goal
            context: Optional context from memory
            
        Returns:
            Plan object
        """
        task = self.create_task(
            "plan_creation",
            {
                "goal": goal,
                "context": context or {}
            }
        )
        task = self.execute(task)
        return task.result if task.result else None
    
    def refine_plan(
        self,
        original_plan: Plan,
        critique: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Plan:
        """
        Refine an existing plan based on critique.
        
        Args:
            original_plan: Plan to refine
            critique: Critique with improvement suggestions
            context: Additional context
            
        Returns:
            Refined Plan
        """
        refined_plan = self.planning_engine.refine_plan(
            original_plan=original_plan,
            critique=critique,
            context=context
        )
        
        # Validate refined plan
        is_valid, issues = self.planning_engine.validate_plan(refined_plan)
        if not is_valid:
            raise ValueError(f"Refined plan is invalid: {', '.join(issues)}")
        
        return refined_plan

