"""
Example script demonstrating the Multi-Agent Market Intelligence System

Usage:
    python scripts/run_agents.py
"""

from app.agents import Orchestrator
from app.vector_db.config import VectorDBConfig
from app.config.settings import get_settings

settings = get_settings()


def main():
    """Run the multi-agent system"""
    
    # Initialize vector DB config
    vector_config = VectorDBConfig(
        persist_directory=settings.vectordb.PERSIST_DIR,
        collection_name=settings.vectordb.COLLECTION_NAME,
        embedding_model=settings.model.EMBEDDING_MODEL
    )
    
    # Create orchestrator
    orchestrator = Orchestrator(vector_db_config=vector_config)
    
    # Example: Research and generate ideas for a topic
    topic = "AI-powered productivity tools for remote teams"
    
    print("=" * 60)
    print("Multi-Agent Market Intelligence System")
    print("=" * 60)
    print(f"\nTopic: {topic}\n")
    
    # Run full pipeline
    result = orchestrator.run_full_pipeline(
        topic=topic,
        generate_ideas=True,
        evaluate_ideas=True,
        num_ideas=5,
        top_k_research=10
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    if result.research_results:
        print(f"\n📚 Research Results:")
        print(f"   Documents found: {len(result.research_results.documents)}")
        print(f"   Key findings: {len(result.research_results.key_findings)}")
        print(f"   Sources: {', '.join(result.research_results.sources[:3])}...")
    
    if result.market_analysis:
        print(f"\n📊 Market Analysis:")
        print(f"   Market Maturity: {result.market_analysis.market_maturity}")
        print(f"   Market Size: {result.market_analysis.market_size}")
        print(f"   Opportunities: {len(result.market_analysis.opportunities)}")
        print(f"   Trends: {', '.join(result.market_analysis.trends[:3])}...")
    
    if result.generated_ideas:
        print(f"\n💡 Generated Ideas ({len(result.generated_ideas)}):")
        for i, idea in enumerate(result.generated_ideas, 1):
            print(f"\n   {i}. {idea.title}")
            print(f"      {idea.description[:100]}...")
            print(f"      Target: {idea.target_audience}")
    
    if result.evaluations:
        print(f"\n📝 Evaluations:")
        for i, eval_result in enumerate(result.evaluations, 1):
            print(f"   Idea {i}:")
            print(f"      Overall Score: {eval_result.overall_score:.2f}/1.0")
            print(f"      Verdict: {eval_result.verdict}")
            print(f"      Strengths: {len(eval_result.strengths)}")
    
    if result.top_ideas:
        print(f"\n🏆 Top {len(result.top_ideas)} Ideas:")
        for i, idea in enumerate(result.top_ideas, 1):
            eval_result = result.evaluations[i-1] if i <= len(result.evaluations) else None
            score = eval_result.overall_score if eval_result else 0.0
            print(f"\n   {i}. {idea.title} (Score: {score:.2f})")
            print(f"      {idea.value_proposition}")
    
    print(f"\n⏱️  Execution Time: {result.execution_time:.2f}s")
    print(f"📄 Summary: {result.summary}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

