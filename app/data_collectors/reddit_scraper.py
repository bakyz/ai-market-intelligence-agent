import json
import os
from datetime import datetime
import praw
from app.config.settings import get_settings


settings = get_settings()

SUBREDDITS = ["startups", "Entrepreneur", "SaaS", "SideProject"]

def scrape_reddit(limit=100):
    reddit = praw.Reddit(
        client_id = os.getenv("REDDIT_CLIENT_ID"),
        client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent = os.getenv("REDDIT_USER_AGENT")
    )

    all_posts = []

    for sub in SUBREDDITS:
        subreddit = reddit.subreddit(sub)
        for post in subreddit.hot(limit=limit):
            all_posts.append({
                "title": post.title,
                "body": post.selftext,
                "score": post.score,
                "comments": post.num_comments,
                "created_at": datetime.fromtimestamp(post.created_utc).isoformat(),
                "source": f"reddit/r/{sub}"
            })
        
    file_path = os.path.join(settings.paths.RAW_DATA, "reddit.json")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False)
    
    print(f"Scraped {len(all_posts)} Reddit posts -> {file_path}")
    
    return file_path

if __name__ == "__main__":
    scrape_reddit(limit=settings.scraper.REDDIT_LIMIT)