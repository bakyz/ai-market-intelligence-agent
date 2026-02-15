from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    MARKET_ANALYST = "market_analyst"
    EVALUATOR = "evaluator"
    IDEA_GENERATOR = "idea_generator"
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ResearchResult:
    query: str
    documents: List[Dict[str, Any]]
    summary: str
    key_findings: List[str]
    sources: List[str]
    timestamp: datetime


@dataclass
class MarketAnalysis:
    topic: str
    market_size: Optional[str]
    trends: List[str]
    opportunities: List[str]
    threats: List[str]
    competitive_landscape: str
    market_maturity: str  
    confidence_score: float  


@dataclass
class IdeaEvaluation:
    idea: str
    feasibility_score: float  
    market_potential_score: float  
    innovation_score: float  
    overall_score: float  
    strengths: List[str]
    weaknesses: List[str]
    risks: List[str]
    recommendations: List[str]
    verdict: str  


@dataclass
class GeneratedIdea:
    title: str
    description: str
    target_audience: str
    value_proposition: str
    key_features: List[str]
    market_opportunity: str
    inspiration_sources: List[str]


@dataclass
class AgentTask:
    task_id: str
    agent_role: AgentRole
    task_type: str
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None


@dataclass
class AgentMessage:
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime


@dataclass
class OrchestrationResult:
    task_id: str
    research_results: Optional[ResearchResult] = None
    market_analysis: Optional[MarketAnalysis] = None
    generated_ideas: List[GeneratedIdea] = None
    evaluations: List[IdeaEvaluation] = None
    top_ideas: List[GeneratedIdea] = None
    summary: str = ""
    execution_time: float = 0.0
    status: TaskStatus = TaskStatus.PENDING


# =========================
# Planning System Schemas
# =========================

@dataclass
class TaskNode:
    """Represents a single task in the task graph"""
    task_id: str
    description: str
    task_type: str
    dependencies: List[str]  # List of task_ids that must complete first
    agent_role: AgentRole
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class Plan:
    """Represents a complete execution plan"""
    plan_id: str
    goal: str
    tasks: List[TaskNode]
    created_at: datetime
    version: int = 1
    metadata: Dict[str, Any] = None


@dataclass
class Critique:
    """Result from critic agent evaluation"""
    completeness_score: float  # 0.0-1.0
    evidence_strength_score: float  # 0.0-1.0
    coherence_score: float  # 0.0-1.0
    actionability_score: float  # 0.0-1.0
    overall_score: float  # 0.0-1.0
    weaknesses: List[str]
    missing_components: List[str]
    improvement_suggestions: List[str]
    should_iterate: bool
    confidence: float  # 0.0-1.0
    timestamp: datetime


# =========================
# Memory System Schemas
# =========================

@dataclass
class MemoryEntry:
    """Single memory entry"""
    memory_id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    memory_type: str  # "action", "reasoning", "result", "feedback"


@dataclass
class Experience:
    """Long-term experience entry"""
    experience_id: str
    goal: str
    plan: Optional[Plan]
    result: Any
    critique: Optional[Critique]
    success: bool
    lessons_learned: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = None


# =========================
# Autonomous Loop Schemas
# =========================

@dataclass
class IterationResult:
    """Result from a single iteration"""
    iteration_number: int
    plan: Plan
    execution_result: Any
    critique: Critique
    execution_time: float
    token_usage: Optional[int] = None
    cost: Optional[float] = None
    timestamp: datetime = None


@dataclass
class AutonomousExecutionResult:
    """Final result from autonomous execution"""
    execution_id: str
    goal: str
    iterations: List[IterationResult]
    final_result: Any
    total_iterations: int
    total_execution_time: float
    total_cost: Optional[float] = None
    total_tokens: Optional[int] = None
    status: TaskStatus = TaskStatus.PENDING
    termination_reason: str = ""  # "threshold_met", "max_iterations", "error", "timeout"

