from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from app.agents.schemas import Experience, IterationResult, AutonomousExecutionResult


class ExperienceLog:
    """
    Logs experiences to disk for persistence and analysis.
    Provides methods to save and load execution history.
    """
    
    def __init__(self, log_directory: str = "data/experience_logs"):
        """
        Initialize experience log.
        
        Args:
            log_directory: Directory to store log files
        """
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_experience(self, experience: Experience) -> Path:
        """
        Log an experience to disk.
        
        Args:
            experience: Experience object to log
            
        Returns:
            Path to the log file
        """
        timestamp = experience.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"experience_{experience.experience_id}_{timestamp}.json"
        filepath = self.log_dir / filename
        
        # Serialize experience
        data = {
            "experience_id": experience.experience_id,
            "goal": experience.goal,
            "success": experience.success,
            "lessons_learned": experience.lessons_learned,
            "timestamp": experience.timestamp.isoformat(),
            "metadata": experience.metadata or {}
        }
        
        # Serialize complex objects as strings (can be improved with proper serialization)
        if experience.plan:
            data["plan"] = {
                "plan_id": experience.plan.plan_id if hasattr(experience.plan, 'plan_id') else None,
                "goal": experience.plan.goal if hasattr(experience.plan, 'goal') else None,
                "task_count": len(experience.plan.tasks) if hasattr(experience.plan, 'tasks') else 0
            }
        
        if experience.critique:
            data["critique"] = {
                "overall_score": experience.critique.overall_score if hasattr(experience.critique, 'overall_score') else None,
                "weaknesses": experience.critique.weaknesses if hasattr(experience.critique, 'weaknesses') else [],
                "improvement_suggestions": experience.critique.improvement_suggestions if hasattr(experience.critique, 'improvement_suggestions') else []
            }
        
        if experience.result:
            # Try to extract summary or serialize as string
            if hasattr(experience.result, 'summary'):
                data["result_summary"] = experience.result.summary
            else:
                data["result"] = str(experience.result)[:1000]  # Truncate long results
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def log_iteration(self, iteration: IterationResult) -> Path:
        """
        Log an iteration result.
        
        Args:
            iteration: IterationResult to log
            
        Returns:
            Path to the log file
        """
        timestamp = iteration.timestamp.isoformat() if iteration.timestamp else datetime.now().isoformat()
        filename = f"iteration_{iteration.iteration_number}_{timestamp.replace(':', '-')}.json"
        filepath = self.log_dir / filename
        
        data = {
            "iteration_number": iteration.iteration_number,
            "execution_time": iteration.execution_time,
            "token_usage": iteration.token_usage,
            "cost": iteration.cost,
            "timestamp": timestamp,
            "critique": {
                "overall_score": iteration.critique.overall_score if hasattr(iteration.critique, 'overall_score') else None,
                "should_iterate": iteration.critique.should_iterate if hasattr(iteration.critique, 'should_iterate') else False
            } if iteration.critique else None
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def log_execution(self, execution: AutonomousExecutionResult) -> Path:
        """
        Log a complete autonomous execution.
        
        Args:
            execution: AutonomousExecutionResult to log
            
        Returns:
            Path to the log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"execution_{execution.execution_id}_{timestamp}.json"
        filepath = self.log_dir / filename
        
        data = {
            "execution_id": execution.execution_id,
            "goal": execution.goal,
            "total_iterations": execution.total_iterations,
            "total_execution_time": execution.total_execution_time,
            "total_cost": execution.total_cost,
            "total_tokens": execution.total_tokens,
            "status": execution.status.value,
            "termination_reason": execution.termination_reason,
            "iterations": [
                {
                    "iteration_number": it.iteration_number,
                    "execution_time": it.execution_time,
                    "critique_score": it.critique.overall_score if it.critique and hasattr(it.critique, 'overall_score') else None
                }
                for it in execution.iterations
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_recent_executions(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Load recent execution logs.
        
        Args:
            n: Number of recent executions to load
            
        Returns:
            List of execution dictionaries
        """
        execution_files = sorted(
            self.log_dir.glob("execution_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:n]
        
        executions = []
        for filepath in execution_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    executions.append(json.load(f))
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        return executions

