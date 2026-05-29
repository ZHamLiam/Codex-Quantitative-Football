import feedparser
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

SOURCES = [
    {"name": "skysports", "url": "https://www.skysports.com/football/rss", "tier": 2},
    {"name": "espn", "url": "https://www.espn.com/espn/rss/soccer/news", "tier": 2},
    {"name": "bbc", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "tier": 2},
    {"name": "goal", "url": "https://www.goal.com/feeds/en/news", "tier": 3},
    {"name": "fourfourtwo", "url": "https://www.fourfourtwo.com/feeds/all", "tier": 3},
]

def _fetch_one(config, max_per_source):
    local_items = []
    try:
        feed = feedparser.parse(config["url"])
        for entry in feed.entries[:max_per_source]:
            local_items.append({
                "source": config["name"],
                "source_tier": config["tier"],
                "title": entry.get("title", ""),
                "summary": entry.get("summary", entry.get("description", "")),
                "url": entry.get("link", ""),
                "published_at": entry.get("published", ""),
            })
    except Exception:
        pass
    return local_items

def fetch_news(max_per_source: int = 15) -> list:
    items = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_fetch_one, cfg, max_per_source): cfg for cfg in SOURCES}
        try:
            for future in as_completed(futures, timeout=10):
                try:
                    items.extend(future.result(timeout=5))
                except Exception:
                    pass
        except FuturesTimeoutError:
            pass  # Some sources timed out, use what we have
    return items

def fetch_news_for_team(team_name: str, max_items: int = 10) -> list:
    all_news = fetch_news(max_per_source=10)
    team_lower = team_name.lower()
    keywords = [team_lower]
    parts = team_lower.split()
    if len(parts) > 1:
        keywords.append(parts[-1])

    filtered = []
    for item in all_news:
        text = (item["title"] + " " + item["summary"]).lower()
        if any(kw in text for kw in keywords):
            filtered.append(item)
    return filtered[:max_items]
