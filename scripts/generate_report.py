"""
Script to generate market intelligence reports

This script can generate reports in multiple ways:
1. From processed data (market_analysis.json)
2. Using the multi-agent system for comprehensive analysis
3. Using the RAG insight generator

Usage:
    python scripts/generate_report.py [--method METHOD] [--topic TOPIC] [--output OUTPUT]
    
Options:
    --method: 'data' (from processed data), 'agents' (multi-agent), 'rag' (RAG insights)
    --topic: Topic for agent-based or RAG-based reports
    --output: Output file path (default: reports/report_YYYYMMDD_HHMMSS.json)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import get_settings
from app.rag.insight_generator import InsightGenerator
from app.rag.retriever import RAGRetriever
from app.vector_db.config import VectorDBConfig
from app.agents import Orchestrator

settings = get_settings()


def generate_report_from_data(output_path: Path) -> dict:
    """Generate report from processed data"""
    processed_file = Path(settings.paths.PROCESSED_DATA) / "market_analysis.json"
    
    if not processed_file.exists():
        raise FileNotFoundError(f"Processed data not found: {processed_file}")
    
    with open(processed_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Aggregate insights
    all_analyses = [record.get("market_analysis", "") for record in data]
    
    # Count sources
    sources = {}
    for record in data:
        source = record.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
    
    # Generate summary using LLM
    from app.llm.client import LLMWrapper
    from app.llm.model_router import ModelRouter
    
    model = ModelRouter.get_model_for_task("synthesis")
    llm = LLMWrapper(model=model)
    
    summary_prompt = f"""Based on {len(data)} market analysis records, generate a comprehensive market intelligence report.

The report should include:
1. Executive Summary
2. Key Market Trends
3. Pain Points Identified
4. Opportunities
5. Recommendations

Analysis excerpts:
{chr(10).join(all_analyses[:10])}

Generate a structured report in JSON format:
{{
    "executive_summary": "...",
    "key_trends": ["...", "..."],
    "pain_points": ["...", "..."],
    "opportunities": ["...", "..."],
    "recommendations": ["...", "..."]
}}"""
    
    response = llm.query(
        summary_prompt,
        system_prompt="You are a senior market intelligence analyst creating executive reports."
    )
    
    try:
        report_data = json.loads(response)
    except json.JSONDecodeError:
        report_data = {
            "executive_summary": response[:500],
            "key_trends": [],
            "pain_points": [],
            "opportunities": [],
            "recommendations": []
        }
    
    # Add metadata
    report = {
        "report_type": "data_analysis",
        "generated_at": datetime.now().isoformat(),
        "data_sources": sources,
        "total_records": len(data),
        "report": report_data
    }
    
    return report


def generate_report_from_agents(topic: str, output_path: Path) -> dict:
    """Generate report using multi-agent system"""
    print(f"🤖 Using multi-agent system for topic: {topic}")
    
    vector_config = VectorDBConfig(
        persist_directory=settings.vectordb.PERSIST_DIR,
        collection_name=settings.vectordb.COLLECTION_NAME,
        embedding_model=settings.model.EMBEDDING_MODEL
    )
    
    orchestrator = Orchestrator(vector_db_config=vector_config)
    
    result = orchestrator.run_full_pipeline(
        topic=topic,
        generate_ideas=True,
        evaluate_ideas=True,
        num_ideas=5,
        top_k_research=10
    )
    
    # Convert to report format
    report = {
        "report_type": "multi_agent",
        "generated_at": datetime.now().isoformat(),
        "topic": topic,
        "execution_time": result.execution_time,
        "research": {
            "summary": result.research_results.summary if result.research_results else "",
            "key_findings": result.research_results.key_findings if result.research_results else [],
            "sources": result.research_results.sources if result.research_results else []
        } if result.research_results else None,
        "market_analysis": {
            "market_size": result.market_analysis.market_size if result.market_analysis else None,
            "market_maturity": result.market_analysis.market_maturity if result.market_analysis else None,
            "trends": result.market_analysis.trends if result.market_analysis else [],
            "opportunities": result.market_analysis.opportunities if result.market_analysis else [],
            "threats": result.market_analysis.threats if result.market_analysis else []
        } if result.market_analysis else None,
        "generated_ideas": [
            {
                "title": idea.title,
                "description": idea.description,
                "target_audience": idea.target_audience,
                "value_proposition": idea.value_proposition,
                "key_features": idea.key_features,
                "market_opportunity": idea.market_opportunity
            }
            for idea in (result.generated_ideas or [])
        ],
        "evaluations": [
            {
                "idea": eval_result.idea[:100] + "..." if len(eval_result.idea) > 100 else eval_result.idea,
                "overall_score": eval_result.overall_score,
                "feasibility_score": eval_result.feasibility_score,
                "market_potential_score": eval_result.market_potential_score,
                "innovation_score": eval_result.innovation_score,
                "verdict": eval_result.verdict,
                "strengths": eval_result.strengths,
                "weaknesses": eval_result.weaknesses,
                "recommendations": eval_result.recommendations
            }
            for eval_result in (result.evaluations or [])
        ],
        "top_ideas": [
            {
                "title": idea.title,
                "description": idea.description,
                "value_proposition": idea.value_proposition
            }
            for idea in (result.top_ideas or [])
        ],
        "summary": result.summary
    }
    
    return report


def generate_report_from_rag(topic: str, output_path: Path) -> dict:
    """Generate report using RAG insight generator"""
    print(f"🔍 Using RAG system for topic: {topic}")
    
    vector_config = VectorDBConfig(
        persist_directory=settings.vectordb.PERSIST_DIR,
        collection_name=settings.vectordb.COLLECTION_NAME,
        embedding_model=settings.model.EMBEDDING_MODEL
    )
    
    retriever = RAGRetriever(vector_config)
    insight_generator = InsightGenerator()
    
    # Retrieve relevant documents
    documents = retriever.retrieve(topic, top_k=10)
    
    # Format context
    context = "\n\n".join([
        f"Document {i+1} (Score: {doc.score:.3f}):\n{doc.text[:500]}..."
        for i, doc in enumerate(documents)
    ])
    
    # Generate insights
    insights = insight_generator.generate(topic, context)
    
    # Create report
    report = {
        "report_type": "rag_insights",
        "generated_at": datetime.now().isoformat(),
        "topic": topic,
        "documents_analyzed": len(documents),
        "insights": {
            "summary": insights.summary,
            "pain_points": insights.pain_points,
            "opportunities": insights.opportunities,
            "signals": insights.signals
        },
        "sources": list(set([doc.metadata.get("source", "unknown") for doc in documents]))
    }
    
    return report


def save_report(report: dict, output_path: Path):
    """Save report to file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Report saved to: {output_path}")


def print_report_summary(report: dict):
    """Print a summary of the report"""
    print("\n" + "=" * 60)
    print("Report Summary")
    print("=" * 60)
    
    report_type = report.get("report_type", "unknown")
    print(f"\n📋 Report Type: {report_type}")
    print(f"📅 Generated: {report.get('generated_at', 'Unknown')}")
    
    if report_type == "data_analysis":
        print(f"📊 Records Analyzed: {report.get('total_records', 0)}")
        report_data = report.get("report", {})
        print(f"📈 Trends Identified: {len(report_data.get('key_trends', []))}")
        print(f"🎯 Opportunities: {len(report_data.get('opportunities', []))}")
    
    elif report_type == "multi_agent":
        print(f"⏱️  Execution Time: {report.get('execution_time', 0):.2f}s")
        if report.get("research"):
            print(f"📚 Research Findings: {len(report['research'].get('key_findings', []))}")
        if report.get("market_analysis"):
            print(f"📊 Market Maturity: {report['market_analysis'].get('market_maturity', 'Unknown')}")
        print(f"💡 Ideas Generated: {len(report.get('generated_ideas', []))}")
        print(f"🏆 Top Ideas: {len(report.get('top_ideas', []))}")
    
    elif report_type == "rag_insights":
        print(f"📄 Documents Analyzed: {report.get('documents_analyzed', 0)}")
        insights = report.get("insights", {})
        print(f"🎯 Pain Points: {len(insights.get('pain_points', []))}")
        print(f"💡 Opportunities: {len(insights.get('opportunities', []))}")
        print(f"📊 Signals: {len(insights.get('signals', []))}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate market intelligence reports")
    parser.add_argument(
        "--method",
        choices=["data", "agents", "rag"],
        default="data",
        help="Report generation method (default: data)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic for agent-based or RAG-based reports (required for agents/rag methods)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: reports/report_YYYYMMDD_HHMMSS.json)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.method in ["agents", "rag"] and not args.topic:
        print(f"❌ Error: --topic is required for method '{args.method}'")
        return 1
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Path(settings.paths.REPORTS)
        output_path = reports_dir / f"report_{timestamp}.json"
    
    print("=" * 60)
    print("Market Intelligence Report Generator")
    print("=" * 60)
    
    try:
        # Generate report based on method
        if args.method == "data":
            print("\n📊 Generating report from processed data...")
            report = generate_report_from_data(output_path)
        
        elif args.method == "agents":
            report = generate_report_from_agents(args.topic, output_path)
        
        elif args.method == "rag":
            report = generate_report_from_rag(args.topic, output_path)
        
        # Save report
        save_report(report, output_path)
        
        # Print summary
        print_report_summary(report)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {str(e)}")
        if args.method == "data":
            print("   Run 'python scripts/run_analysis.py' first to process data.")
        return 1
    except Exception as e:
        print(f"\n❌ Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

