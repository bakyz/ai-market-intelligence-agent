from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import uuid

from app.agents.schemas import MemoryEntry


class ShortTermMemory:
    """
    Manages short-term memory for current session.
    Stores recent actions, reasoning, and context.
    """
    
    def __init__(self, max_size: int = 50):
        """
        Initialize short-term memory.
        
        Args:
            max_size: Maximum number of entries to keep
        """
        self.max_size = max_size
        self.memories: deque = deque(maxlen=max_size)
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()
    
    def push(
        self,
        content: str,
        memory_type: str = "action",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Add a new memory entry.
        
        Args:
            content: Memory content
            memory_type: Type of memory ("action", "reasoning", "result", "feedback")
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        memory_id = f"stm_{uuid.uuid4().hex[:12]}"
        
        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(),
            memory_type=memory_type
        )
        
        self.memories.append(entry)
        return memory_id
    
    def get_recent(self, n: int = 5, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """
        Get recent memory entries.
        
        Args:
            n: Number of entries to retrieve
            memory_type: Optional filter by memory type
            
        Returns:
            List of MemoryEntry objects (most recent first)
        """
        entries = list(self.memories)
        
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        
        # Return most recent n entries
        return entries[-n:] if len(entries) > n else entries
    
    def get_all(self, memory_type: Optional[str] = None) -> List[MemoryEntry]:
        """
        Get all memory entries.
        
        Args:
            memory_type: Optional filter by memory type
            
        Returns:
            List of all MemoryEntry objects
        """
        entries = list(self.memories)
        
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        
        return entries
    
    def get_context(self, max_tokens: int = 1000) -> str:
        """
        Get formatted context string from recent memories.
        
        Args:
            max_tokens: Approximate max tokens (rough estimate)
            
        Returns:
            Formatted context string
        """
        entries = list(self.memories)
        context_parts = []
        char_count = 0
        
        # Start from most recent
        for entry in reversed(entries):
            entry_str = f"[{entry.memory_type}] {entry.content}\n"
            if char_count + len(entry_str) > max_tokens * 4:  # Rough estimate: 4 chars per token
                break
            context_parts.insert(0, entry_str)
            char_count += len(entry_str)
        
        return "".join(context_parts)
    
    def clear(self):
        """Clear all short-term memories"""
        self.memories.clear()
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "session_start": self.session_start,
            "memory_count": len(self.memories),
            "memory_types": list(set(e.memory_type for e in self.memories))
        }

