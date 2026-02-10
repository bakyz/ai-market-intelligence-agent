import json
from typing import List, Dict, Any
from datetime import datetime

from app.agents.base_agent import BaseAgent
from app.agents.schemas import AgentRole, AgentTask, TaskStatus, ResearchResult
from app.rag.retriever import RAGRetriever
from app.vector_db.config import VectorDBConfig


class ResearcherAgent(BaseAgent):
    
    def __init__(self, vector_db_config: VectorDBConfig):
        super().__init__(role=AgentRole.RESEARCHER)
        self.retriever = RAGRetriever(vector_db_config)
    
    def _get_default_system_prompt(self) -> str:
        return """You are a senior research analyst specializing in startup and technology markets.
Your role is to:
- Extract key insights from research documents
- Identify patterns and trends
- Summarize findings clearly and concisely
- Highlight the most important information"""
    
    def execute(self, task: AgentTask) -> AgentTask:
        try:
            self._update_task_status(task, TaskStatus.IN_PROGRESS)
            
            query = task.input_data.get("query", "")
            top_k = task.input_data.get("top_k", 10)
            
            documents = self.retriever.retrieve(query, top_k=top_k)
            
            context = self._format_documents(documents)
            
            summary_prompt = f"""Based on the following research documents, provide:
1. A comprehensive summary (2-3 paragraphs)
2. Key findings (bullet points)

Query: {query}

Documents:
{context}

Format your response as JSON:
{{
    "summary": "...",
    "key_findings": ["...", "..."]
}}"""
            
            response = self.query_llm(summary_prompt)
            
            try:
                parsed = json.loads(response)
                summary = parsed.get("summary", "")
                key_findings = parsed.get("key_findings", [])
            except json.JSONDecodeError:
                summary = response
                key_findings = self._extract_findings_from_text(response)
            
            sources = [doc.metadata.get("source", "unknown") for doc in documents]
            sources = list(set(sources))  
        
            result = ResearchResult(
                query=query,
                documents=[
                    {
                        "id": doc.id,
                        "text": doc.text,
                        "metadata": doc.metadata,
                        "score": doc.score
                    }
                    for doc in documents
                ],
                summary=summary,
                key_findings=key_findings,
                sources=sources,
                timestamp=datetime.now()
            )
            
            self._update_task_status(task, TaskStatus.COMPLETED, result=result)
            self.log_task(task)
            
        except Exception as e:
            self._update_task_status(
                task,
                TaskStatus.FAILED,
                error=str(e)
            )
            self.log_task(task)
        
        return task
    
    def _format_documents(self, documents: List) -> str:
        """Format documents for LLM context"""
        formatted = []
        for i, doc in enumerate(documents, 1):
            formatted.append(
                f"Document {i} (Relevance: {doc.score:.3f}):\n"
                f"Source: {doc.metadata.get('source', 'unknown')}\n"
                f"Content: {doc.text[:500]}...\n"
            )
        return "\n".join(formatted)
    
    def _extract_findings_from_text(self, text: str) -> List[str]:
        """Extract findings from text if JSON parsing fails"""
        lines = text.split("\n")
        findings = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("*") or 
                        (line[0].isdigit() and "." in line[:3])):
                findings.append(line.lstrip("-* ").split(". ", 1)[-1])
        return findings[:10]  
    
    def research(self, query: str, top_k: int = 10) -> ResearchResult:
        """Convenience method for quick research"""
        task = self.create_task("research", {"query": query, "top_k": top_k})
        task = self.execute(task)
        return task.result


