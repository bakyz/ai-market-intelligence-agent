from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

from app.llm.client import LLMWrapper
from app.llm.model_router import ModelRouter
from app.agents.schemas import AgentRole, TaskStatus, AgentTask


class BaseAgent(ABC):
    def __init__(self, role: AgentRole, model: Optional[str] = None, system_prompt: Optional[str] = None):
        self.role = role
        self.model = model or ModelRouter.get_model_for_task("synthesis")
        self.llm = LLMWrapper(model=self.model)
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.task_history: list[AgentTask] = []
    
    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        pass

    @abstractmethod
    def execute(self, task: AgentTask) -> AgentTask:
        pass

    def create_task(self, task_type: str, input_data: Dict[str, Any]) -> AgentTask:
        task = AgentTask(task_id=str(uuid.uuid4()), 
            agent_role=self.role, 
            task_type=task_type,
            input_data=input_data,
            status=TaskStatus.PENDING,
            created_at=datetime.now())
        return task
    
    def _update_task_status(self, task: AgentTask, status: TaskStatus, result: Optional[Any] = None, error: Optional[str] = None) -> AgentTask:
        task.status = status
        if result:
            task.result = result
        if error:
            task.error = error
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
        return task
    
    def query_llm(self, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None) -> str:
        sys_prompt = system_prompt or self.system_prompt
        return self.llm.query(prompt, system_prompt=sys_prompt)
    
    def log_task(self, task: AgentTask):
        self.task_history.append(task)
    
    def get_task_history(self) -> list[AgentTask]:
        return self.task_history
    
    def __repr__(self)-> str:
        return f"{self.__class__.__name__}(role={self.role.value})"
    
