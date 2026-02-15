import json
from typing import List, Dict, Any
from datetime import datetime
import uuid

from app.llm.client import LLMWrapper
from app.llm.model_router import ModelRouter
from app.agents.schemas import AgentRole, TaskNode, TaskStatus


class GoalDecomposer:
    """Decomposes high-level goals into structured task sequences"""
    
    def __init__(self, model: str = None):
        self.model = model or ModelRouter.get_model_for_task("synthesis")
        self.llm = LLMWrapper(model=self.model)
    
    def decompose(self, goal: str, context: Dict[str, Any] = None) -> List[TaskNode]:
        """
        Break down a high-level goal into a sequence of tasks.
        
        Args:
            goal: High-level objective (e.g., "Find underserved SaaS opportunities in AI dev tools")
            context: Optional context from previous executions or memory
            
        Returns:
            List of TaskNode objects representing the execution plan
        """
        context_str = ""
        if context:
            context_str = f"\nContext from previous work:\n{json.dumps(context, indent=2)}"
        
        decomposition_prompt = f"""Break down the following high-level goal into a structured sequence of specific, actionable tasks.

Goal: {goal}
{context_str}

For market intelligence and research goals, typical steps include:
1. Information retrieval/research
2. Data analysis and pattern identification
3. Opportunity identification
4. Evaluation and scoring
5. Synthesis and reporting

Provide a JSON array of tasks, each with:
{{
    "description": "Clear, specific task description",
    "task_type": "research|analysis|generation|evaluation|synthesis",
    "dependencies": ["task_id_1", "task_id_2"],  // Empty array for first task
    "agent_role": "researcher|market_analyst|idea_generator|evaluator",
    "input_data": {{"key": "value"}}  // Task-specific parameters
}}

Ensure:
- Tasks are ordered logically (dependencies make sense)
- Each task is specific and actionable
- Dependencies form a valid DAG (no cycles)
- Agent roles match task types appropriately

Return ONLY the JSON array, no additional text."""

        response = self.llm.query(
            decomposition_prompt,
            system_prompt="You are an expert at breaking down complex goals into structured, executable task sequences. Be specific and practical."
        )
        
        try:
            tasks_data = json.loads(response)
            if not isinstance(tasks_data, list):
                tasks_data = [tasks_data]
        except json.JSONDecodeError:
            tasks_data = self._parse_fallback(response, goal)
        
        # Convert to TaskNode objects
        task_nodes = []
        task_id_map = {}  # Map from description to task_id for dependency resolution
        
        for i, task_data in enumerate(tasks_data):
            task_id = f"task_{i+1}_{uuid.uuid4().hex[:8]}"
            task_id_map[i] = task_id
            
            # Resolve dependencies
            dependencies = []
            if "dependencies" in task_data:
                # Convert dependency indices or descriptions to task_ids
                for dep in task_data["dependencies"]:
                    if isinstance(dep, int) and dep in task_id_map:
                        dependencies.append(task_id_map[dep])
                    elif isinstance(dep, str):
                        # Try to find by description
                        for idx, td in enumerate(tasks_data):
                            if td.get("description") == dep and idx in task_id_map:
                                dependencies.append(task_id_map[idx])
                                break
            
            # Map string agent_role to enum
            agent_role_str = task_data.get("agent_role", "researcher")
            agent_role = self._map_agent_role(agent_role_str)
            
            task_node = TaskNode(
                task_id=task_id,
                description=task_data.get("description", f"Task {i+1}"),
                task_type=task_data.get("task_type", "research"),
                dependencies=dependencies,
                agent_role=agent_role,
                input_data=task_data.get("input_data", {}),
                status=TaskStatus.PENDING
            )
            task_nodes.append(task_node)
        
        return task_nodes
    
    def _map_agent_role(self, role_str: str) -> AgentRole:
        """Map string role to AgentRole enum"""
        role_map = {
            "researcher": AgentRole.RESEARCHER,
            "market_analyst": AgentRole.MARKET_ANALYST,
            "idea_generator": AgentRole.IDEA_GENERATOR,
            "evaluator": AgentRole.EVALUATOR,
        }
        return role_map.get(role_str.lower(), AgentRole.RESEARCHER)
    
    def _parse_fallback(self, text: str, goal: str) -> List[Dict[str, Any]]:
        """Fallback parser if JSON parsing fails"""
        # Simple heuristic: split by numbered items
        lines = text.split("\n")
        tasks = []
        current_task = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_task:
                    tasks.append(current_task)
                    current_task = {}
                continue
            
            # Check for numbered items
            if line[0].isdigit() and (". " in line[:5] or ") " in line[:5]):
                if current_task:
                    tasks.append(current_task)
                current_task = {
                    "description": line.split(". ", 1)[-1] if ". " in line else line.split(") ", 1)[-1],
                    "task_type": "research",
                    "dependencies": [],
                    "agent_role": "researcher",
                    "input_data": {}
                }
            elif ":" in line and current_task:
                key, value = line.split(":", 1)
                key = key.lower().strip()
                if key in ["description", "task_type", "agent_role"]:
                    current_task[key] = value.strip()
        
        if current_task:
            tasks.append(current_task)
        
        # Ensure at least one task
        if not tasks:
            tasks = [{
                "description": f"Research and analyze: {goal}",
                "task_type": "research",
                "dependencies": [],
                "agent_role": "researcher",
                "input_data": {"query": goal}
            }]
        
        return tasks

