"""
Script to run data collection scrapers (Reddit and Hacker News)

Usage:
    python scripts/run_scrapers.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.data_collectors.reddit_scraper import scrape_reddit
from app.data_collectors.hn_scraper import scrape_hackernews
from app.config.settings import get_settings

settings = get_settings()


def main():
    """Run all scrapers"""
    print("=" * 60)
    print("Data Collection Scrapers")
    print("=" * 60)
    
    # Check for required environment variables for Reddit
    reddit_required = ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT"]
    reddit_missing = [var for var in reddit_required if not os.getenv(var)]
    
    if reddit_missing:
        print(f"\n⚠️  Warning: Missing Reddit environment variables: {', '.join(reddit_missing)}")
        print("   Reddit scraping will be skipped.")
        print("   Set these in your .env file or environment.")
        reddit_enabled = False
    else:
        reddit_enabled = True
    
    results = {}
    
    # Scrape Reddit
    if reddit_enabled:
        try:
            print("\n📱 Scraping Reddit...")
            reddit_path = scrape_reddit(limit=settings.scraper.REDDIT_LIMIT)
            results["reddit"] = {
                "status": "success",
                "path": reddit_path
            }
            print(f"✅ Reddit scraping completed")
        except Exception as e:
            print(f"❌ Reddit scraping failed: {str(e)}")
            results["reddit"] = {
                "status": "failed",
                "error": str(e)
            }
    else:
        results["reddit"] = {
            "status": "skipped",
            "reason": "Missing environment variables"
        }
    
    # Scrape Hacker News
    try:
        print("\n📰 Scraping Hacker News...")
        hn_path = scrape_hackernews(limit=settings.scraper.HN_LIMIT)
        results["hackernews"] = {
            "status": "success",
            "path": hn_path
        }
        print(f"✅ Hacker News scraping completed")
    except Exception as e:
        print(f"❌ Hacker News scraping failed: {str(e)}")
        results["hackernews"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # Summary
    print("\n" + "=" * 60)
    print("Scraping Summary")
    print("=" * 60)
    
    for source, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌" if result["status"] == "failed" else "⏭️"
        print(f"{status_icon} {source.capitalize()}: {result['status']}")
        if result["status"] == "success":
            print(f"   Path: {result['path']}")
        elif result["status"] == "failed":
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Check if we have data for analysis
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    if success_count > 0:
        print(f"\n✅ Successfully scraped {success_count} source(s)")
        print("   Next step: Run 'python scripts/run_analysis.py' to process the data")
    else:
        print("\n⚠️  No data was successfully scraped. Please check errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

