from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from app.agents.schemas import Experience
from app.vector_db.config import VectorDBConfig
from app.vector_db.chroma_client import ChromaVectorDB
from app.vector_db.embedding_service import EmbeddingService


class LongTermMemory:
    """
    Manages long-term memory using vector store.
    Stores experiences, research reports, trends, and feedback.
    """
    
    def __init__(self, vector_db_config: VectorDBConfig, collection_name: str = "long_term_memory"):
        """
        Initialize long-term memory.
        
        Args:
            vector_db_config: Vector database configuration
            collection_name: Name of the collection for long-term memory
        """
        self.config = vector_db_config
        # Create separate config for memory collection
        memory_config = VectorDBConfig(
            persist_directory=vector_db_config.persist_directory,
            collection_name=collection_name,
            embedding_model=vector_db_config.embedding_model,
            batch_size=vector_db_config.batch_size,
            max_retries=vector_db_config.max_retries
        )
        
        self.db = ChromaVectorDB(memory_config)
        self.embedder = EmbeddingService(
            model=memory_config.embedding_model,
            max_retries=memory_config.max_retries
        )
    
    def store_experience(
        self,
        goal: str,
        plan: Any = None,
        result: Any = None,
        critique: Any = None,
        success: bool = True,
        lessons_learned: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Store an experience in long-term memory.
        
        Args:
            goal: The goal that was pursued
            plan: The plan that was executed
            result: The execution result
            critique: Critique of the result
            success: Whether the execution was successful
            lessons_learned: List of lessons learned
            metadata: Additional metadata
            
        Returns:
            Experience ID
        """
        experience_id = f"exp_{uuid.uuid4().hex[:12]}"
        
        # Create searchable text
        text_parts = [f"Goal: {goal}"]
        
        if plan:
            if hasattr(plan, 'goal'):
                text_parts.append(f"Plan: {plan.goal}")
            if hasattr(plan, 'tasks'):
                task_descriptions = [task.description for task in plan.tasks]
                text_parts.append(f"Tasks: {', '.join(task_descriptions)}")
        
        if result:
            if hasattr(result, 'summary'):
                text_parts.append(f"Result: {result.summary}")
            else:
                text_parts.append(f"Result: {str(result)[:500]}")
        
        if critique:
            if hasattr(critique, 'weaknesses'):
                text_parts.append(f"Weaknesses: {', '.join(critique.weaknesses)}")
            if hasattr(critique, 'improvement_suggestions'):
                text_parts.append(f"Suggestions: {', '.join(critique.improvement_suggestions)}")
        
        if lessons_learned:
            text_parts.append(f"Lessons: {', '.join(lessons_learned)}")
        
        searchable_text = "\n".join(text_parts)
        
        # Create experience object
        experience = Experience(
            experience_id=experience_id,
            goal=goal,
            plan=plan,
            result=result,
            critique=critique,
            success=success,
            lessons_learned=lessons_learned or [],
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Generate embedding
        embedding = self.embedder.embed(searchable_text)
        
        # Store in vector DB
        metadata_dict = {
            "experience_id": experience_id,
            "goal": goal,
            "success": str(success),
            "timestamp": experience.timestamp.isoformat(),
            "lessons_count": len(lessons_learned or []),
            **metadata
        }
        
        # Serialize complex objects
        if plan:
            metadata_dict["has_plan"] = "true"
        if result:
            metadata_dict["has_result"] = "true"
        if critique:
            metadata_dict["has_critique"] = "true"
            if hasattr(critique, 'overall_score'):
                metadata_dict["critique_score"] = str(critique.overall_score)
        
        self.db.add_documents(
            ids=[experience_id],
            documents=[searchable_text],
            embeddings=[embedding],
            metadatas=[metadata_dict]
        )
        
        return experience_id
    
    def search_experiences(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant experiences.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of experience dictionaries
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Query vector DB
        results = self.db.query(query_embedding, n_results=top_k)
        
        experiences = []
        
        if results and "ids" in results and len(results["ids"]) > 0:
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)
            
            for i, exp_id in enumerate(ids):
                # Apply metadata filters if provided
                if filter_metadata:
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    if not all(metadata.get(k) == str(v) for k, v in filter_metadata.items()):
                        continue
                
                experiences.append({
                    "experience_id": exp_id,
                    "content": documents[i] if i < len(documents) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "similarity": 1.0 - distances[i] if i < len(distances) else 0.0
                })
        
        return experiences
    
    def retrieve_relevant_memory(
        self,
        current_goal: str,
        context: str = "",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieve relevant memories for current context.
        
        Args:
            current_goal: Current goal being pursued
            context: Additional context
            top_k: Number of memories to retrieve
            
        Returns:
            Dictionary with relevant memories and context
        """
        # Combine goal and context for search
        search_query = f"{current_goal}\n{context}".strip()
        
        # Search for similar experiences
        experiences = self.search_experiences(search_query, top_k=top_k)
        
        # Also search for successful experiences
        successful_experiences = self.search_experiences(
            search_query,
            top_k=2,
            filter_metadata={"success": "True"}
        )
        
        return {
            "similar_experiences": experiences,
            "successful_experiences": successful_experiences,
            "context": self._format_memories_for_context(experiences + successful_experiences)
        }
    
    def _format_memories_for_context(self, experiences: List[Dict[str, Any]]) -> str:
        """Format memories into context string"""
        if not experiences:
            return ""
        
        context_parts = ["Relevant past experiences:"]
        for exp in experiences[:5]:  # Limit to top 5
            content = exp.get("content", "")
            metadata = exp.get("metadata", {})
            similarity = exp.get("similarity", 0.0)
            
            context_parts.append(
                f"- [Similarity: {similarity:.2f}] {content[:200]}..."
            )
        
        return "\n".join(context_parts)

