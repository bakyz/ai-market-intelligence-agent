"""
Script to run data analysis pipeline

This script:
1. Loads raw scraped data (Reddit and Hacker News)
2. Preprocesses and cleans the text
3. Generates embeddings
4. Runs LLM analysis to extract market insights
5. Saves processed data to data/processed/

Usage:
    python scripts/run_analysis.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.data_pipeline import run_pipeline, load_json_records
from app.config.settings import get_settings

settings = get_settings()


def main():
    """Run the data analysis pipeline"""
    print("=" * 60)
    print("Data Analysis Pipeline")
    print("=" * 60)
    
    raw_path = Path(settings.paths.RAW_DATA)
    processed_path = Path(settings.paths.PROCESSED_DATA)
    
    # Check if raw data exists
    reddit_file = raw_path / "reddit.json"
    hn_file = raw_path / "hn.json"
    
    files_exist = []
    if reddit_file.exists():
        files_exist.append(("Reddit", reddit_file))
    if hn_file.exists():
        files_exist.append(("Hacker News", hn_file))
    
    if not files_exist:
        print(f"\n❌ No raw data files found in {raw_path}")
        print("   Please run 'python scripts/run_scrapers.py' first to collect data.")
        return 1
    
    print(f"\n📂 Found {len(files_exist)} data source(s):")
    for name, file_path in files_exist:
        try:
            records = load_json_records(file_path)
            print(f"   ✅ {name}: {len(records)} records")
        except Exception as e:
            print(f"   ❌ {name}: Error loading - {str(e)}")
            return 1
    
    # Check for OpenAI API key
    if not settings.OPENAI_API_KEY:
        print("\n❌ OPENAI_API_KEY not found in settings")
        print("   Please set it in your .env file or environment variables.")
        return 1
    
    print(f"\n🔧 Configuration:")
    print(f"   Embedding Model: {settings.model.EMBEDDING_MODEL}")
    print(f"   Analysis Model: {settings.model_routing.ANALYSIS_MODEL}")
    print(f"   Temperature: {settings.model.TEMPERATURE}")
    print(f"   Max Tokens: {settings.model.MAX_TOKENS}")
    
    # Run pipeline
    try:
        print("\n🚀 Starting analysis pipeline...")
        print("   This may take a while depending on the amount of data...")
        
        output_file = run_pipeline()
        
        print("\n" + "=" * 60)
        print("Pipeline Completed Successfully!")
        print("=" * 60)
        print(f"\n✅ Processed data saved to: {output_file}")
        
        # Show statistics
        try:
            import json
            with open(output_file, "r", encoding="utf-8") as f:
                processed_data = json.load(f)
            
            print(f"\n📊 Statistics:")
            print(f"   Total records processed: {len(processed_data)}")
            
            # Count by source
            sources = {}
            for record in processed_data:
                source = record.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            print(f"   Sources:")
            for source, count in sources.items():
                print(f"      - {source}: {count} records")
            
            print(f"\n💡 Next steps:")
            print(f"   1. Index data into vector DB (if not already done)")
            print(f"   2. Run 'python scripts/generate_report.py' to generate insights")
            print(f"   3. Or use the multi-agent system: 'python scripts/run_agents.py'")
            
        except Exception as e:
            print(f"   ⚠️  Could not load statistics: {str(e)}")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {str(e)}")
        print("   Make sure raw data files exist in data/raw/")
        return 1
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

