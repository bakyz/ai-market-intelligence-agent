from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    MARKET_ANALYST = "market_analyst"
    EVALUATOR = "evaluator"
    IDEA_GENERATOR = "idea_generator"


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

