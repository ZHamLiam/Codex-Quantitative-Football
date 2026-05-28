import feedparser, httpx
from datetime import datetime, timedelta

SOURCES = [
    {"name": "skysports", "url": "https://www.skysports.com/football/rss", "tier": 2},
    {"name": "espn", "url": "https://www.espn.com/espn/rss/soccer/news", "tier": 2},
    {"name": "bbc", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "tier": 2},
    {"name": "goal", "url": "https://www.goal.com/feeds/en/news", "tier": 3},
    {"name": "fourfourtwo", "url": "https://www.fourfourtwo.com/feeds/all", "tier": 3},
]

def fetch_news(max_per_source: int = 15) -> list:
    items = []
    for config in SOURCES:
        try:
            feed = feedparser.parse(config["url"])
            for entry in feed.entries[:max_per_source]:
                items.append({
                    "source": config["name"],
                    "source_tier": config["tier"],
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", entry.get("description", "")),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                })
        except Exception:
            continue
    return items

def fetch_news_for_team(team_name: str, max_items: int = 10) -> list:
    """Filter news mentioning a specific team."""
    all_news = fetch_news(max_per_source=10)
    team_lower = team_name.lower()
    keywords = [team_lower]
    # Add common variations
    parts = team_lower.split()
    if len(parts) > 1:
        keywords.append(parts[-1])  # e.g., "Germain" for "Paris Saint Germain"

    filtered = []
    for item in all_news:
        text = (item["title"] + " " + item["summary"]).lower()
        if any(kw in text for kw in keywords):
            filtered.append(item)
    return filtered[:max_items]