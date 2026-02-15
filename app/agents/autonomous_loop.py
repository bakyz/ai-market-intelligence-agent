import time
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from app.agents.planner_agent import PlannerAgent
from app.agents.executor_agent import ExecutorAgent
from app.agents.critic_agent import CriticAgent
from app.agents.self_reflection import SelfReflection
from app.agents.schemas import (
    Plan, Critique, IterationResult, AutonomousExecutionResult, TaskStatus
)
from app.memory.memory_store import MemoryStore
from app.memory.experience_log import ExperienceLog
from app.vector_db.config import VectorDBConfig


class AutonomousLoop:
    """
    Autonomous execution loop that plans, executes, critiques, and iterates.
    Implements the full autonomous agent workflow with safety guards.
    """
    
    def __init__(
        self,
        vector_db_config: VectorDBConfig,
        max_iterations: int = 5,
        score_threshold: float = 0.75,
        max_cost: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout_seconds: Optional[float] = None
    ):
        """
        Initialize autonomous loop.
        
        Args:
            vector_db_config: Vector database configuration
            max_iterations: Maximum number of iterations
            score_threshold: Score threshold to stop iterating
            max_cost: Maximum cost in dollars (None for no limit)
            max_tokens: Maximum token usage (None for no limit)
            timeout_seconds: Maximum execution time in seconds (None for no limit)
        """
        # Initialize agents
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(vector_db_config)
        self.critic = CriticAgent()
        
        # Initialize memory and logging
        self.memory = MemoryStore(vector_db_config)
        self.experience_log = ExperienceLog()
        
        # Initialize self-reflection
        self.reflection = SelfReflection(self.memory)
        
        # Safety guards
        self.max_iterations = max_iterations
        self.score_threshold = score_threshold
        self.max_cost = max_cost
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        
        # Tracking
        self.total_cost = 0.0
        self.total_tokens = 0
    
    def run(
        self,
        goal: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> AutonomousExecutionResult:
        """
        Run the autonomous execution loop.
        
        Args:
            goal: High-level goal to achieve
            initial_context: Optional initial context
            
        Returns:
            AutonomousExecutionResult with final results
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        iterations = []
        current_plan: Optional[Plan] = None
        final_result = None
        termination_reason = ""
        
        # Log goal to short-term memory
        self.memory.push_short_term(
            content=f"Goal: {goal}",
            memory_type="action",
            metadata={"execution_id": execution_id}
        )
        
        # Retrieve relevant past experiences
        if initial_context is None:
            initial_context = {}
        
        relevant_memory = self.memory.retrieve_relevant_memory(goal, top_k=3)
        if relevant_memory.get("context"):
            initial_context["past_experiences"] = relevant_memory["context"]
        
        try:
            for iteration in range(1, self.max_iterations + 1):
                iteration_start = time.time()
                
                # Check timeout
                if self.timeout_seconds and (time.time() - start_time) > self.timeout_seconds:
                    termination_reason = "timeout"
                    break
                
                print(f"\n{'='*60}")
                print(f"Iteration {iteration}/{self.max_iterations}")
                print(f"{'='*60}")
                
                # Step 1: Plan (or refine plan)
                print(f"📋 Planning...")
                if iteration == 1:
                    # Create initial plan
                    current_plan = self.planner.create_plan(
                        goal=goal,
                        context=initial_context
                    )
                    self.memory.push_short_term(
                        content=f"Created plan with {len(current_plan.tasks)} tasks",
                        memory_type="action"
                    )
                else:
                    # Refine plan based on previous critique
                    if iterations[-1].critique:
                        current_plan = self.planner.refine_plan(
                            original_plan=current_plan,
                            critique=iterations[-1].critique,
                            context=initial_context
                        )
                        self.memory.push_short_term(
                            content=f"Refined plan (v{current_plan.version})",
                            memory_type="reasoning"
                        )
                
                if not current_plan:
                    termination_reason = "planning_failed"
                    break
                
                print(f"✅ Plan created: {len(current_plan.tasks)} tasks")
                
                # Step 2: Execute plan
                print(f"🚀 Executing plan...")
                execution_result = self.executor.run_plan(current_plan)
                execution_time = time.time() - iteration_start
                
                # Extract final result (use last completed task result or aggregated result)
                if execution_result.get("final_results"):
                    final_result = list(execution_result["final_results"].values())[-1]
                else:
                    final_result = execution_result
                
                self.memory.push_short_term(
                    content=f"Execution completed: {execution_result.get('completed_tasks', 0)} tasks",
                    memory_type="result"
                )
                
                print(f"✅ Execution completed in {execution_time:.2f}s")
                
                # Step 3: Critique result
                print(f"🔍 Critiquing result...")
                critique = self.critic.evaluate(
                    result=final_result,
                    goal=goal,
                    context=self.memory.get_recent_context()
                )
                
                print(f"📊 Critique Score: {critique.overall_score:.2f}/1.0")
                print(f"   - Completeness: {critique.completeness_score:.2f}")
                print(f"   - Evidence: {critique.evidence_strength_score:.2f}")
                print(f"   - Coherence: {critique.coherence_score:.2f}")
                print(f"   - Actionability: {critique.actionability_score:.2f}")
                
                if critique.weaknesses:
                    print(f"⚠️  Weaknesses: {', '.join(critique.weaknesses[:2])}")
                
                # Step 4: Self-reflection
                reflection = self.reflection.reflect(
                    goal=goal,
                    plan=current_plan,
                    result=final_result,
                    critique=critique,
                    execution_time=execution_time
                )
                
                # Create iteration result
                iteration_result = IterationResult(
                    iteration_number=iteration,
                    plan=current_plan,
                    execution_result=execution_result,
                    critique=critique,
                    execution_time=execution_time,
                    timestamp=datetime.now()
                )
                
                iterations.append(iteration_result)
                
                # Log iteration
                self.experience_log.log_iteration(iteration_result)
                
                # Check if we should continue
                should_continue = self.reflection.should_continue_iterating(
                    critique=critique,
                    iteration_number=iteration,
                    max_iterations=self.max_iterations,
                    threshold=self.score_threshold
                )
                
                if not should_continue:
                    if critique.overall_score >= self.score_threshold:
                        termination_reason = "threshold_met"
                        print(f"✅ Quality threshold met ({critique.overall_score:.2f} >= {self.score_threshold})")
                    else:
                        termination_reason = "max_iterations"
                        print(f"⏹️  Reached maximum iterations")
                    break
                
                # Check safety guards
                if self.max_cost and self.total_cost >= self.max_cost:
                    termination_reason = "max_cost"
                    print(f"⚠️  Cost limit reached: ${self.total_cost:.2f}")
                    break
                
                if self.max_tokens and self.total_tokens >= self.max_tokens:
                    termination_reason = "max_tokens"
                    print(f"⚠️  Token limit reached: {self.total_tokens}")
                    break
                
                print(f"🔄 Iterating again (score {critique.overall_score:.2f} < threshold {self.score_threshold})...")
            
            # Final iteration check
            if not termination_reason:
                termination_reason = "max_iterations"
            
            total_execution_time = time.time() - start_time
            
            # Create final result
            result = AutonomousExecutionResult(
                execution_id=execution_id,
                goal=goal,
                iterations=iterations,
                final_result=final_result,
                total_iterations=len(iterations),
                total_execution_time=total_execution_time,
                total_cost=self.total_cost,
                total_tokens=self.total_tokens,
                status=TaskStatus.COMPLETED if final_result else TaskStatus.FAILED,
                termination_reason=termination_reason
            )
            
            # Log execution
            self.experience_log.log_execution(result)
            
            # Store final experience
            final_critique = iterations[-1].critique if iterations else None
            critique_metadata = {}
            if final_critique:
                critique_metadata = {
                    'completeness': final_critique.completeness_score,
                    'evidence': final_critique.evidence_strength_score,
                    'coherence': final_critique.coherence_score,
                    'actionability': final_critique.actionability_score,
                    'overall': final_critique.overall_score
                }
            else:
                critique_metadata = {}
            
            self.memory.store_experience(
                goal=goal,
                plan=current_plan,
                result=final_result,
                critique=None,
                success=result.status == TaskStatus.COMPLETED,
                lessons_learned=reflection.get("lessons_learned", []) if iterations else [],
                metadata={
                    "execution_id": execution_id,
                    "total_iterations": len(iterations),
                    "termination_reason": termination_reason,
                    **critique_metadata
                })
            
            print(f"\n{'='*60}")
            print(f"✅ Autonomous execution completed")
            print(f"   Iterations: {len(iterations)}")
            print(f"   Total time: {total_execution_time:.2f}s")
            print(f"   Termination: {termination_reason}")
            if iterations:
                print(f"   Final score: {iterations[-1].critique.overall_score:.2f}/1.0")
            print(f"{'='*60}\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Autonomous execution failed: {str(e)}")
            
            result = AutonomousExecutionResult(
                execution_id=execution_id,
                goal=goal,
                iterations=iterations,
                final_result=final_result,
                total_iterations=len(iterations),
                total_execution_time=time.time() - start_time,
                total_cost=self.total_cost,
                total_tokens=self.total_tokens,
                status=TaskStatus.FAILED,
                termination_reason=f"error: {str(e)}"
            )
            
            return result
    
    def get_execution_summary(self, result: AutonomousExecutionResult) -> str:
        """Get a formatted summary of execution"""
        summary_parts = [
            f"Execution ID: {result.execution_id}",
            f"Goal: {result.goal}",
            f"Iterations: {result.total_iterations}",
            f"Total Time: {result.total_execution_time:.2f}s",
            f"Status: {result.status.value}",
            f"Termination: {result.termination_reason}",
        ]
        
        if result.iterations:
            scores = [it.critique.overall_score for it in result.iterations if it.critique]
            if scores:
                summary_parts.append(f"Score Progression: {' → '.join(f'{s:.2f}' for s in scores)}")
                summary_parts.append(f"Final Score: {scores[-1]:.2f}/1.0")
        
        return "\n".join(summary_parts)

