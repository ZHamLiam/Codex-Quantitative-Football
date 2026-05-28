def cluster_news(news_items: list) -> dict:
    clusters = {}
    for item in news_items:
        title = item.get("title", "")
        key = _extract_team_topic(title)
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(item)
    return clusters

def verify_claim(cluster: list) -> dict:
    if not cluster:
        return {"consensus_score": 0, "verdict": "unconfirmed"}

    tier_weights = {1: 1.0, 2: 0.75, 3: 0.6, 4: 0.35, 5: 0.15}
    total_weight = sum(tier_weights.get(item.get("source_tier", 3), 0.1) for item in cluster)
    high_tier = any(item.get("source_tier", 5) <= 2 for item in cluster)

    if total_weight >= 3 and high_tier:
        return {"consensus_score": 80, "verdict": "confirmed"}
    elif total_weight >= 1.5:
        return {"consensus_score": 50, "verdict": "disputed"}
    else:
        return {"consensus_score": 20, "verdict": "unconfirmed"}

def detect_smoke(cluster: list) -> bool:
    tiers = [item.get("source_tier", 5) for item in cluster]
    if all(t >= 4 for t in tiers):
        return True
    if len(set(item.get("source", "") for item in cluster)) == 1:
        return True
    return False

def _extract_team_topic(title: str) -> str:
    keywords = ["受伤", "injury", "首发", "lineup", "转会", "transfer", "战术", "tactic", "轮休", "rest"]
    for kw in keywords:
        if kw.lower() in title.lower():
            return kw
    return "other"
