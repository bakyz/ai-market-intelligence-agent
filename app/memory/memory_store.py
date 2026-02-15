from typing import Dict, Any, Optional
from app.memory.short_term_memory import ShortTermMemory
from app.memory.long_term_memory import LongTermMemory
from app.vector_db.config import VectorDBConfig


class MemoryStore:
    """
    Unified interface for both short-term and long-term memory.
    Provides a single entry point for memory operations.
    """
    
    def __init__(self, vector_db_config: VectorDBConfig, short_term_max_size: int = 50):
        """
        Initialize memory store.
        
        Args:
            vector_db_config: Vector database configuration
            short_term_max_size: Maximum size for short-term memory
        """
        self.short_term = ShortTermMemory(max_size=short_term_max_size)
        self.long_term = LongTermMemory(vector_db_config)
    
    def push_short_term(
        self,
        content: str,
        memory_type: str = "action",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add entry to short-term memory"""
        return self.short_term.push(content, memory_type, metadata)
    
    def get_recent_context(self, n: int = 5, max_tokens: int = 1000) -> str:
        """Get recent context from short-term memory"""
        return self.short_term.get_context(max_tokens)
    
    def store_experience(
        self,
        goal: str,
        plan: Any = None,
        result: Any = None,
        critique: Any = None,
        success: bool = True,
        lessons_learned: list = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store experience in long-term memory"""
        return self.long_term.store_experience(
            goal, plan, result, critique, success, lessons_learned, metadata
        )
    
    def retrieve_relevant_memory(
        self,
        current_goal: str,
        context: str = "",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Retrieve relevant memories for current context"""
        return self.long_term.retrieve_relevant_memory(current_goal, context, top_k)
    
    def get_full_context(
        self,
        current_goal: str,
        short_term_n: int = 5,
        long_term_k: int = 3
    ) -> str:
        """
        Get full context combining short-term and long-term memory.
        
        Args:
            current_goal: Current goal
            short_term_n: Number of recent short-term memories
            long_term_k: Number of relevant long-term memories
            
        Returns:
            Combined context string
        """
        short_term_context = self.short_term.get_context(max_tokens=500)
        long_term_memories = self.retrieve_relevant_memory(current_goal, top_k=long_term_k)
        long_term_context = long_term_memories.get("context", "")
        
        context_parts = []
        
        if short_term_context:
            context_parts.append("=== Recent Session Context ===")
            context_parts.append(short_term_context)
        
        if long_term_context:
            context_parts.append("\n=== Relevant Past Experiences ===")
            context_parts.append(long_term_context)
        
        return "\n".join(context_parts) if context_parts else ""
    
    def clear_short_term(self):
        """Clear short-term memory"""
        self.short_term.clear()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return self.short_term.get_session_info()

