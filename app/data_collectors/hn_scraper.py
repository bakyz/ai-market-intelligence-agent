import requests
import json
import os
from datetime import datetime
from app.config.settings import get_settings

settings = get_settings()

HN_API_URL = "http://hn.algolia.com/api/v1/search?tags=front_page"

def scrape_hackernews(limit=100):
    all_posts = []

    response = requests.get(HN_API_URL)
    response.raise_for_status()
    data = response.json()

    for post in data.get("hits", [])[:limit]:
        all_posts.append({
            "title": post.get("title"),
            "body": post.get("story_text") or "",
            "score": post.get("points"),
            "comments": post.get("num_comments"),
            "created_at": datetime.fromtimestamp(post.get("created_at_i")).isoformat()
            if post.get("created_at_i") else None,
            "source": "hackernews"
        })

    file_path = os.path.join(settings.paths.RAW_DATA, "hn.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, indent=2, ensure_ascii=False)

    print(f"Scraped {len(all_posts)} Hacker News posts -> {file_path}")
    return file_path

if __name__ == "__main__":
    scrape_hackernews(limit=settings.scraper.X_LIMIT)
