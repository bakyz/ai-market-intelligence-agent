from typing import List, Dict, Set, Optional, Any
from collections import deque

from app.agents.schemas import TaskNode, TaskStatus


class TaskGraph:
    """
    Represents a directed acyclic graph (DAG) of tasks.
    Handles topological sorting and dependency resolution.
    """
    
    def __init__(self, tasks: List[TaskNode]):
        self.tasks = tasks
        self.task_map: Dict[str, TaskNode] = {task.task_id: task for task in tasks}
        self._validate_dag()
    
    def _validate_dag(self):
        """Validate that the task graph is a valid DAG (no cycles)"""
        # Build adjacency list
        graph = {task_id: [] for task_id in self.task_map.keys()}
        for task in self.tasks:
            for dep_id in task.dependencies:
                if dep_id in self.task_map:
                    graph[dep_id].append(task.task_id)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for neighbor in graph.get(node_id, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for task_id in self.task_map.keys():
            if task_id not in visited:
                if has_cycle(task_id):
                    raise ValueError(f"Cycle detected in task graph involving task: {task_id}")
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """
        Get tasks that are ready to execute (all dependencies completed).
        
        Returns:
            List of TaskNode objects ready for execution
        """
        ready = []
        
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            all_deps_complete = True
            for dep_id in task.dependencies:
                dep_task = self.task_map.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    all_deps_complete = False
                    break
            
            if all_deps_complete:
                ready.append(task)
        
        return ready
    
    def get_execution_order(self) -> List[List[TaskNode]]:
        """
        Get tasks in topological order, grouped by execution level.
        Tasks in the same level can be executed in parallel.
        
        Returns:
            List of lists, where each inner list contains tasks that can run in parallel
        """
        # Build dependency graph
        in_degree = {task_id: 0 for task_id in self.task_map.keys()}
        graph = {task_id: [] for task_id in self.task_map.keys()}
        
        for task in self.tasks:
            for dep_id in task.dependencies:
                if dep_id in self.task_map:
                    in_degree[task.task_id] += 1
                    graph[dep_id].append(task.task_id)
        
        # Topological sort with levels
        levels = []
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        
        while queue:
            level = []
            level_size = len(queue)
            
            for _ in range(level_size):
                task_id = queue.popleft()
                level.append(self.task_map[task_id])
                
                # Process dependents
                for dependent_id in graph[task_id]:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
            
            if level:
                levels.append(level)
        
        return levels
    
    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """Get a task by its ID"""
        return self.task_map.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None):
        """Update the status of a task"""
        task = self.task_map.get(task_id)
        if task:
            task.status = status
            if result is not None:
                task.result = result
            if error:
                task.error = error
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed"""
        return all(
            task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED
            for task in self.tasks
        )
    
    def get_failed_tasks(self) -> List[TaskNode]:
        """Get all tasks that failed"""
        return [task for task in self.tasks if task.status == TaskStatus.FAILED]
    
    def get_completed_tasks(self) -> List[TaskNode]:
        """Get all completed tasks"""
        return [task for task in self.tasks if task.status == TaskStatus.COMPLETED]

