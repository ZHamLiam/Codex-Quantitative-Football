import feedparser

SOURCES = {
    "skysports": {"url": "https://www.skysports.com/football/rss", "tier": 2},
    "espn": {"url": "https://www.espn.com/espn/rss/soccer/news", "tier": 2},
    "bbc": {"url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "tier": 2},
}

def fetch_news(max_per_source: int = 10) -> list:
    items = []
    for name, config in SOURCES.items():
        try:
            feed = feedparser.parse(config["url"])
            for entry in feed.entries[:max_per_source]:
                items.append({
                    "source": name,
                    "source_tier": config["tier"],
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", ""),
                })
        except Exception:
            continue
    return items
