from llm.client import chat

SYSTEM_PROMPT = """You are a quantitative football analyst. Analyze the simulation results and provide insights in Chinese.

Output format (2-4 sentences total):
1. Main prediction: who is favored and by how much
2. Upset analysis: flag if underdog win probability > 30% (explain why - specific factors driving the underdog's chance)
3. Big score analysis: flag if expected total goals > 2.8 (explain what conditions could lead to high scoring)
4. Risk summary: one sentence on key risk

Rules:
- Be specific: mention actual percentages and factor names
- For upsets: explain which factors are giving the underdog an edge (e.g., "South Africa's 33% win probability is driven by high uncertainty in World Cup MD1 and Mexico's weak recent form")
- For big scores: mention what tactical factors could lead to goals
- If upset probability < 30%, say "爆冷可能性较低" but still mention the data
- If expected goals < 2.5, say "预计进球偏少" 
- Keep total under 250 characters"""

def interpret_results(sim_result: dict, advice: dict, match_info: dict) -> str:
    # Compute upset and big-score metrics
    home_pct = sim_result.get("home_win_pct", 50)
    draw_pct = sim_result.get("draw_pct", 25)
    away_pct = sim_result.get("away_win_pct", 25)
    expected_goals = sim_result.get("expected_goals", 2.5)
    variance = sim_result.get("variance", 1.0)

    # Determine favorite and underdog
    if home_pct > away_pct:
        fav_name = match_info.get("home_team", "Home")
        fav_pct = home_pct
        dog_name = match_info.get("away_team", "Away")
        dog_pct = away_pct
    else:
        fav_name = match_info.get("away_team", "Away")
        fav_pct = away_pct
        dog_name = match_info.get("home_team", "Home")
        dog_pct = home_pct

    upset_flag = "HIGH" if dog_pct > 30 else "LOW"
    goals_flag = "HIGH" if expected_goals > 2.8 else "LOW"

    # Build detailed context
    user_msg = f"""Match: {match_info.get('home_team', '?')} vs {match_info.get('away_team', '?')}
League: {match_info.get('league', '?')} | Stage: {match_info.get('stage', '?')}

Simulation results:
- {match_info.get('home_team', 'Home')} win: {home_pct}%
- Draw: {draw_pct}%
- {match_info.get('away_team', 'Away')} win: {away_pct}%
- Expected total goals: {expected_goals}
- Variance (uncertainty): {variance}

Upset analysis:
- Favorite: {fav_name} ({fav_pct}%)
- Underdog: {dog_name} ({dog_pct}%)
- Upset risk: {upset_flag} (threshold: 30%)

Big score analysis:
- Expected goals: {expected_goals}
- Big score risk: {goals_flag} (threshold: 2.8)

Strategy:
- Best pick: {advice.get('best_pick', '?')}
- Expected value: {advice.get('expected_value', 0)}
- Suggestion: {advice.get('suggestion', '?')}
- Risk level: {advice.get('risk_level', '?')}
"""

    resp = chat(SYSTEM_PROMPT, user_msg, temperature=0.3)
    return resp

def get_upset_metrics(sim_result: dict, match_info: dict) -> dict:
    """Return structured upset/big-score metrics for frontend display."""
    home_pct = sim_result.get("home_win_pct", 50)
    away_pct = sim_result.get("away_win_pct", 25)
    expected_goals = sim_result.get("expected_goals", 2.5)

    if home_pct > away_pct:
        dog_pct = away_pct
        dog_name = match_info.get("away_team", "Away")
        fav_name = match_info.get("home_team", "Home")
    else:
        dog_pct = home_pct
        dog_name = match_info.get("home_team", "Home")
        fav_name = match_info.get("away_team", "Away")

    upset_threshold = 30
    goals_threshold = 2.8

    return {
        "favorite": fav_name,
        "underdog": dog_name,
        "underdog_win_pct": round(dog_pct, 1),
        "upset_risk": "HIGH" if dog_pct > upset_threshold else "LOW",
        "upset_threshold": upset_threshold,
        "expected_goals": expected_goals,
        "big_score_risk": "HIGH" if expected_goals > goals_threshold else "LOW",
        "goals_threshold": goals_threshold,
    }