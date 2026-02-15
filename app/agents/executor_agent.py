from typing import List, Dict, Any, Optional
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import AgentRole, AgentTask, TaskStatus, TaskNode, Plan
from app.agents.researcher_agent import ResearcherAgent
from app.agents.market_agent import MarketAgent
from app.agents.idea_generator_agent import IdeaGeneratorAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.vector_db.config import VectorDBConfig


class ExecutorAgent(BaseAgent):
    """
    Agent responsible for executing plans.
    Coordinates with specialized agents to execute tasks.
    """
    
    def __init__(self, vector_db_config: VectorDBConfig):
        super().__init__(role=AgentRole.EXECUTOR)
        
        # Initialize specialized agents
        self.researcher = ResearcherAgent(vector_db_config)
        self.market_agent = MarketAgent()
        self.idea_generator = IdeaGeneratorAgent()
        self.evaluator = EvaluatorAgent()
        
        # Map agent roles to agent instances
        self.agent_map = {
            AgentRole.RESEARCHER: self.researcher,
            AgentRole.MARKET_ANALYST: self.market_agent,
            AgentRole.IDEA_GENERATOR: self.idea_generator,
            AgentRole.EVALUATOR: self.evaluator
        }
    
    def _get_default_system_prompt(self) -> str:
        return """You are an execution coordinator. Your role is to:
- Execute tasks according to a plan
- Coordinate with specialized agents
- Track task dependencies
- Handle errors gracefully
- Report execution status"""
    
    def execute(self, task: AgentTask) -> AgentTask:
        """
        Execute a plan execution task.
        
        Expected input_data:
            - plan: Plan (required)
        """
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
            plan = task.input_data.get("plan")
            if not plan or not isinstance(plan, Plan):
                raise ValueError("Execution task requires 'plan' in input_data")
            
            # Execute plan
            execution_result = self.run_plan(plan)
            
            self._update_task_status(task, TaskStatus.COMPLETED, result=execution_result)
            self.log_task(task)
            
        except Exception as e:
            self._update_task_status(task, TaskStatus.FAILED, error=str(e))
            self.log_task(task)
        
        return task
    
    def run_plan(self, plan: Plan) -> Dict[str, Any]:
        """
        Execute a complete plan.
        
        Args:
            plan: Plan to execute
            
        Returns:
            Dictionary with execution results
        """
        from app.planning.task_graph import TaskGraph
        
        graph = TaskGraph(plan.tasks)
        execution_order = graph.get_execution_order()
        
        results = {}
        execution_log = []
        
        # Execute tasks level by level
        for level, tasks in enumerate(execution_order):
            level_results = {}
            
            for task_node in tasks:
                try:
                    # Get appropriate agent
                    agent = self.agent_map.get(task_node.agent_role)
                    if not agent:
                        raise ValueError(f"No agent available for role: {task_node.agent_role}")
                    
                    # Create agent task from task node
                    agent_task = agent.create_task(
                        task_type=task_node.task_type,
                        input_data=task_node.input_data
                    )
                    
                    # Execute task
                    agent_task = agent.execute(agent_task)
                    
                    # Update task node status
                    graph.update_task_status(
                        task_node.task_id,
                        agent_task.status,
                        result=agent_task.result,
                        error=agent_task.error
                    )
                    
                    level_results[task_node.task_id] = {
                        "status": agent_task.status.value,
                        "result": agent_task.result,
                        "error": agent_task.error
                    }
                    
                    execution_log.append({
                        "task_id": task_node.task_id,
                        "description": task_node.description,
                        "status": agent_task.status.value,
                        "level": level
                    })
                    
                except Exception as e:
                    graph.update_task_status(
                        task_node.task_id,
                        TaskStatus.FAILED,
                        error=str(e)
                    )
                    level_results[task_node.task_id] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    execution_log.append({
                        "task_id": task_node.task_id,
                        "description": task_node.description,
                        "status": "failed",
                        "error": str(e),
                        "level": level
                    })
            
            results[f"level_{level}"] = level_results
        
        # Collect final results
        completed_tasks = graph.get_completed_tasks()
        failed_tasks = graph.get_failed_tasks()
        
        return {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "execution_log": execution_log,
            "results": results,
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "is_complete": graph.is_complete(),
            "final_results": {task.task_id: task.result for task in completed_tasks}
        }

