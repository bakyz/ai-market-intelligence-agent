from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.schemas import Critique
from app.memory.memory_store import MemoryStore


class SelfReflection:
    """
    Handles self-reflection and learning from execution results.
    Integrates with memory system to store lessons learned.
    """
    
    def __init__(self, memory_store: MemoryStore):
        """
        Initialize self-reflection system.
        
        Args:
            memory_store: Memory store for storing experiences
        """
        self.memory = memory_store
    
    def reflect(
        self,
        goal: str,
        plan: Any,
        result: Any,
        critique: Critique,
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Perform self-reflection on an execution.
        
        Args:
            goal: Original goal
            plan: Executed plan
            result: Execution result
            critique: Critique of the result
            execution_time: Time taken for execution
            
        Returns:
            Dictionary with reflection insights
        """
        # Extract lessons learned
        lessons_learned = self._extract_lessons(critique, result)
        
        # Determine success
        success = critique.overall_score >= 0.7 and not critique.should_iterate
        
        # Store in long-term memory
        experience_id = self.memory.store_experience(
            goal=goal,
            plan=plan,
            result=result,
            critique=critique,
            success=success,
            lessons_learned=lessons_learned,
            metadata={
                "execution_time": execution_time,
                "critique_scores": {
                    "completeness": critique.completeness_score,
                    "evidence": critique.evidence_strength_score,
                    "coherence": critique.coherence_score,
                    "actionability": critique.actionability_score,
                    "overall": critique.overall_score
                }
            }
        )
        
        # Log to short-term memory
        reflection_summary = self._create_reflection_summary(critique, lessons_learned)
        self.memory.push_short_term(
            content=reflection_summary,
            memory_type="reasoning",
            metadata={
                "experience_id": experience_id,
                "overall_score": critique.overall_score,
                "should_iterate": critique.should_iterate
            }
        )
        
        return {
            "experience_id": experience_id,
            "lessons_learned": lessons_learned,
            "success": success,
            "reflection_summary": reflection_summary
        }
    
    def _extract_lessons(self, critique: Critique, result: Any) -> list:
        """Extract lessons learned from critique and result"""
        lessons = []
        
        # Lessons from weaknesses
        if critique.weaknesses:
            lessons.append(f"Identified weaknesses: {', '.join(critique.weaknesses[:3])}")
        
        # Lessons from missing components
        if critique.missing_components:
            lessons.append(f"Missing components to address: {', '.join(critique.missing_components[:3])}")
        
        # Lessons from improvement suggestions
        if critique.improvement_suggestions:
            lessons.append(f"Key improvements: {', '.join(critique.improvement_suggestions[:3])}")
        
        # Score-based lessons
        if critique.completeness_score < 0.6:
            lessons.append("Need to improve completeness of analysis")
        if critique.evidence_strength_score < 0.6:
            lessons.append("Need stronger evidence and data support")
        if critique.coherence_score < 0.6:
            lessons.append("Need to improve logical coherence")
        if critique.actionability_score < 0.6:
            lessons.append("Need more actionable recommendations")
        
        return lessons if lessons else ["Execution completed with acceptable quality"]
    
    def _create_reflection_summary(self, critique: Critique, lessons: list) -> str:
        """Create a summary of the reflection"""
        parts = [
            f"Reflection Summary:",
            f"Overall Score: {critique.overall_score:.2f}/1.0",
            f"Should Iterate: {'Yes' if critique.should_iterate else 'No'}",
        ]
        
        if critique.weaknesses:
            parts.append(f"Weaknesses: {', '.join(critique.weaknesses[:2])}")
        
        if lessons:
            parts.append(f"Lessons: {', '.join(lessons[:2])}")
        
        return "\n".join(parts)
    
    def should_continue_iterating(
        self,
        critique: Critique,
        iteration_number: int,
        max_iterations: int,
        threshold: float = 0.75
    ) -> bool:
        """
        Determine if we should continue iterating.
        
        Args:
            critique: Current critique
            iteration_number: Current iteration number
            max_iterations: Maximum allowed iterations
            threshold: Score threshold to stop iterating
            
        Returns:
            True if should continue, False otherwise
        """
        # Don't continue if we've hit max iterations
        if iteration_number >= max_iterations:
            return False
        
        # Don't continue if score is above threshold and critique says not to iterate
        if critique.overall_score >= threshold and not critique.should_iterate:
            return False
        
        # Continue if critique says we should iterate
        if critique.should_iterate:
            return True
        
        # Continue if score is below threshold
        if critique.overall_score < threshold:
            return True
        
        return False

