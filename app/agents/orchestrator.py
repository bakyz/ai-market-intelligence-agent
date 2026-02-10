import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.researcher_agent import ResearcherAgent
from app.agents.market_agent import MarketAgent
from app.agents.evaluator_agent import EvaluatorAgent
from app.agents.idea_generator_agent import IdeaGeneratorAgent
from app.agents.schemas import (
    AgentRole, AgentTask, TaskStatus, OrchestrationResult,
    ResearchResult, MarketAnalysis, GeneratedIdea, IdeaEvaluation
)
from app.vector_db.config import VectorDBConfig


class Orchestrator:
    """Orchestrates the multi-agent system to complete complex tasks"""
    
    def __init__(self, vector_db_config: VectorDBConfig):
        self.researcher = ResearcherAgent(vector_db_config)
        self.market_agent = MarketAgent()
        self.evaluator = EvaluatorAgent()
        self.idea_generator = IdeaGeneratorAgent()
        self.execution_history: List[OrchestrationResult] = []
    
    def run_full_pipeline(
        self,
        topic: str,
        generate_ideas: bool = True,
        evaluate_ideas: bool = True,
        num_ideas: int = 5,
        top_k_research: int = 10
    ) -> OrchestrationResult:
        """
        Run the complete pipeline:
        1. Research the topic
        2. Analyze the market
        3. Generate ideas (if requested)
        4. Evaluate ideas (if requested)
        5. Return top ideas
        
        Args:
            topic: The topic to research and generate ideas for
            generate_ideas: Whether to generate ideas
            evaluate_ideas: Whether to evaluate generated ideas
            num_ideas: Number of ideas to generate
            top_k_research: Number of research documents to retrieve
            
        Returns:
            OrchestrationResult with all findings
        """
        start_time = time.time()
        result = OrchestrationResult(
            task_id=f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=TaskStatus.IN_PROGRESS
        )
        
        try:
            print(f"🔍 Researching: {topic}")
            research_task = self.researcher.create_task(
                "research",
                {"query": topic, "top_k": top_k_research}
            )
            research_task = self.researcher.execute(research_task)
            
            if research_task.status == TaskStatus.COMPLETED:
                result.research_results = research_task.result
                print(f"✅ Research completed: {len(research_task.result.documents)} documents found")
            else:
                print(f"❌ Research failed: {research_task.error}")
                result.status = TaskStatus.FAILED
                return result
            
            print(f"📊 Analyzing market: {topic}")
            market_task = self.market_agent.create_task(
                "market_analysis",
                {
                    "topic": topic,
                    "research_result": result.research_results
                }
            )
            market_task = self.market_agent.execute(market_task)
            
            if market_task.status == TaskStatus.COMPLETED:
                result.market_analysis = market_task.result
                print(f"✅ Market analysis completed: {market_task.result.market_maturity} market")
            else:
                print(f"❌ Market analysis failed: {market_task.error}")
            
            if generate_ideas:
                print(f"💡 Generating {num_ideas} ideas...")
                idea_task = self.idea_generator.create_task(
                    "idea_generation",
                    {
                        "topic": topic,
                        "num_ideas": num_ideas,
                        "research_result": result.research_results,
                        "market_analysis": result.market_analysis
                    }
                )
                idea_task = self.idea_generator.execute(idea_task)
                
                if idea_task.status == TaskStatus.COMPLETED:
                    result.generated_ideas = idea_task.result
                    print(f"✅ Generated {len(idea_task.result)} ideas")
                else:
                    print(f"❌ Idea generation failed: {idea_task.error}")
            
            if evaluate_ideas and result.generated_ideas:
                print(f"📝 Evaluating {len(result.generated_ideas)} ideas...")
                evaluations = []
                
                for idea in result.generated_ideas:
                    eval_task = self.evaluator.create_task(
                        "idea_evaluation",
                        {
                            "idea_obj": idea,
                            "market_analysis": result.market_analysis
                        }
                    )
                    eval_task = self.evaluator.execute(eval_task)
                    
                    if eval_task.status == TaskStatus.COMPLETED:
                        evaluations.append(eval_task.result)
                    else:
                        print(f"⚠️ Evaluation failed for idea: {idea.title}")
                
                result.evaluations = evaluations
                print(f"✅ Evaluated {len(evaluations)} ideas")
                
                if evaluations:
                    result.top_ideas = self._rank_ideas(
                        result.generated_ideas,
                        evaluations
                    )
                    print(f"🏆 Top {len(result.top_ideas)} ideas selected")
            
            result.summary = self._generate_summary(result)
            result.execution_time = time.time() - start_time
            result.status = TaskStatus.COMPLETED
            
            print(f"\n✅ Pipeline completed in {result.execution_time:.2f}s")
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.summary = f"Pipeline failed: {str(e)}"
            result.execution_time = time.time() - start_time
            print(f"❌ Pipeline failed: {str(e)}")
        
        self.execution_history.append(result)
        return result
    
    def _rank_ideas(
        self,
        ideas: List[GeneratedIdea],
        evaluations: List[IdeaEvaluation]
    ) -> List[GeneratedIdea]:
        """Rank ideas based on evaluations and return top ones"""
        if len(ideas) != len(evaluations):
            return ideas[:3] 
        
        idea_eval_pairs = list(zip(ideas, evaluations))
        idea_eval_pairs.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return [idea for idea, _ in idea_eval_pairs[:3]]
    
    def _generate_summary(self, result: OrchestrationResult) -> str:
        """Generate a summary of the orchestration result"""
        summary_parts = []
        
        if result.research_results:
            summary_parts.append(
                f"Research: Found {len(result.research_results.documents)} relevant documents "
                f"with {len(result.research_results.key_findings)} key findings."
            )
        
        if result.market_analysis:
            summary_parts.append(
                f"Market: {result.market_analysis.market_maturity} market with "
                f"{len(result.market_analysis.opportunities)} opportunities identified."
            )
        
        if result.generated_ideas:
            summary_parts.append(
                f"Ideas: Generated {len(result.generated_ideas)} startup ideas."
            )
        
        if result.evaluations:
            avg_score = sum(e.overall_score for e in result.evaluations) / len(result.evaluations)
            summary_parts.append(
                f"Evaluation: Average score {avg_score:.2f}/1.0 across {len(result.evaluations)} ideas."
            )
        
        if result.top_ideas:
            summary_parts.append(
                f"Top Ideas: Selected {len(result.top_ideas)} highest-potential ideas."
            )
        
        return " ".join(summary_parts)
    
    def get_execution_history(self) -> List[OrchestrationResult]:
        """Get execution history"""
        return self.execution_history
    
    def __repr__(self) -> str:
        return f"Orchestrator(agents=[Researcher, Market, Evaluator, IdeaGenerator])"



