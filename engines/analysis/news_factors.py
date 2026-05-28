import json
from llm.client import chat
from engines.data.news.aggregator import fetch_news

SYSTEM_PROMPT = """You are a football analyst. Given recent news articles, extract structured data about the teams and match.

Output ONLY valid JSON with this exact structure:
{
    "squad_integrity": {"team_name": score_0_to_100, ...},
    "chemistry": {"team_name": score_0_to_100, ...},
    "morale": {"team_name": score_0_to_100, ...},
    "tactics_notes": {"team_name": "brief note", ...},
    "key_injuries": ["player: team, status"],
    "referee_style": {"name": "strict/lenient/average", "avg_cards": number},
    "weather_impact": 45_to_55_number,
    "confidence": 0_to_1_number
}

Rules:
- squad_integrity: 100 = full strength, <70 = key players missing
- chemistry: high if team has played together recently
- morale: high if on winning streak, low if losing/controversy
- If no info about a factor, use 50 as default
- confidence: how reliable the news sources seem (high if multiple sources agree)
- Be conservative - don't make up data, only extract what's mentioned in the news"""

def analyze_news_for_match(home_team: str, away_team: str) -> dict:
    """Fetch news and use LLM to extract factor data."""
    news = fetch_news(10)

    # Build a text summary of news
    news_text = ""
    for item in news[:15]:
        news_text += "[" + item["source"] + "] " + item["title"] + "\n"
        if item.get("summary"):
            news_text += item["summary"][:200] + "\n"
        news_text += "\n"

    if len(news_text) < 50:
        return {
            "squad_integrity": {home_team: 80, away_team: 80},
            "chemistry": {home_team: 50, away_team: 50},
            "morale": {home_team: 50, away_team: 50},
            "confidence": 0.3,
            "source": "no_news"
        }

    user_msg = "Match: " + home_team + " vs " + away_team + "\n\nRecent news:\n" + news_text[:3000]
    resp = chat(SYSTEM_PROMPT, user_msg, temperature=0.1)

    try:
        # Extract JSON from response
        start = resp.find("{")
        end = resp.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(resp[start:end])
            data["source"] = "rss_llm"
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "squad_integrity": {home_team: 80, away_team: 80},
        "chemistry": {home_team: 50, away_team: 50},
        "morale": {home_team: 50, away_team: 50},
        "confidence": 0.3,
        "source": "llm_parse_error"
    }

def enrich_factors(base_inputs: dict, news_data: dict, home_team: str, away_team: str) -> dict:
    """Merge news-derived factors into base factor inputs."""
    enriched = dict(base_inputs)

    # Squad integrity from news
    si = news_data.get("squad_integrity", {})
    if home_team in si:
        enriched["阵容完整度"] = si[home_team]
    elif away_team in si:
        enriched["阵容完整度"] = 100 - (si[away_team] - 50)

    # Chemistry
    chem = news_data.get("chemistry", {})
    if home_team in chem:
        enriched["配合默契度"] = chem[home_team]

    # Morale
    morale = news_data.get("morale", {})
    if home_team in morale:
        enriched["近期士气"] = morale[home_team]

    # Referee style
    ref = news_data.get("referee_style", {})
    if ref.get("avg_cards"):
        cards = ref["avg_cards"]
        enriched["裁判风格"] = max(30, min(80, 50 + (cards - 3.5) * 15))

    # Weather
    if "weather_impact" in news_data:
        enriched["天气"] = news_data["weather_impact"]

    # Confidence affects all factor confidences
    if "confidence" in news_data:
        conf = news_data["confidence"]
        for key in list(enriched.keys()):
            if not key.endswith("_confidence"):
                enriched[key + "_confidence"] = min(1.0, enriched.get(key + "_confidence", 0.6) + conf * 0.2)

    return enriched