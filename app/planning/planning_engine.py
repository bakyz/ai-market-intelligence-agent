from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.planning.goal_decomposer import GoalDecomposer
from app.planning.task_graph import TaskGraph
from app.agents.schemas import Plan, TaskNode


class PlanningEngine:
    """Orchestrates the planning process"""
    
    def __init__(self, model: str = None):
        self.decomposer = GoalDecomposer(model=model)
    
    def create_plan(
        self,
        goal: str,
        context: Dict[str, Any] = None,
        plan_id: str = None,
        version: int = 1
    ) -> Plan:
        """
        Create a complete execution plan from a high-level goal.
        
        Args:
            goal: High-level objective
            context: Optional context from memory or previous executions
            plan_id: Optional plan ID (generated if not provided)
            version: Plan version number
            
        Returns:
            Plan object with task graph
        """
        if plan_id is None:
            plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Decompose goal into tasks
        tasks = self.decomposer.decompose(goal, context)
        
        # Create plan
        plan = Plan(
            plan_id=plan_id,
            goal=goal,
            tasks=tasks,
            created_at=datetime.now(),
            version=version,
            metadata=context or {}
        )
        
        return plan
    
    def refine_plan(
        self,
        original_plan: Plan,
        critique: Any,
        context: Dict[str, Any] = None
    ) -> Plan:
        """
        Refine an existing plan based on critique and feedback.
        
        Args:
            original_plan: The original plan to refine
            critique: Critique object with improvement suggestions
            context: Additional context
            
        Returns:
            Refined Plan with updated tasks
        """
        # Build context from original plan and critique
        refinement_context = {
            "original_plan": {
                "goal": original_plan.goal,
                "tasks": [task.description for task in original_plan.tasks]
            },
            "critique": {
                "weaknesses": critique.weaknesses if hasattr(critique, 'weaknesses') else [],
                "missing_components": critique.missing_components if hasattr(critique, 'missing_components') else [],
                "improvement_suggestions": critique.improvement_suggestions if hasattr(critique, 'improvement_suggestions') else []
            }
        }
        
        if context:
            refinement_context.update(context)
        
        # Create refined plan
        refined_plan = self.create_plan(
            goal=original_plan.goal,
            context=refinement_context,
            plan_id=f"{original_plan.plan_id}_v{original_plan.version + 1}",
            version=original_plan.version + 1
        )
        
        return refined_plan
    
    def validate_plan(self, plan: Plan) -> tuple[bool, List[str]]:
        """
        Validate that a plan is well-formed.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not plan.goal:
            issues.append("Plan has no goal")
        
        if not plan.tasks:
            issues.append("Plan has no tasks")
        
        # Validate task graph
        try:
            graph = TaskGraph(plan.tasks)
        except ValueError as e:
            issues.append(f"Task graph validation failed: {str(e)}")
            return False, issues
        
        # Check for orphaned tasks (tasks with dependencies that don't exist)
        task_ids = {task.task_id for task in plan.tasks}
        for task in plan.tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    issues.append(f"Task {task.task_id} depends on non-existent task {dep_id}")
        
        return len(issues) == 0, issues

