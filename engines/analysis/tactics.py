def calc_possession_style(possession_pct: float) -> float:
    if possession_pct is None:
        return 50.0
    return min(possession_pct, 100.0)

def calc_attack_style(fast_break_ratio: float = 0.3, cross_ratio: float = 0.3, through_ratio: float = 0.4) -> dict:
    total = fast_break_ratio + cross_ratio + through_ratio
    return {"fast_break": fast_break_ratio/total, "cross": cross_ratio/total, "through": through_ratio/total}

def calc_defense_style(ppda: float = 10) -> str:
    if ppda <= 8:
        return "high_press"
    elif ppda <= 14:
        return "mid_block"
    return "low_block"

def calc_style_matchup(home_style: dict, away_style: dict) -> float:
    score = 50.0
    if home_style.get("defense") == "high_press" and away_style.get("attack", {}).get("fast_break", 0) > 0.4:
        score -= 15
    elif away_style.get("defense") == "high_press" and home_style.get("attack", {}).get("fast_break", 0) > 0.4:
        score += 15
    if home_style.get("defense") == "low_block" and away_style.get("attack", {}).get("through", 0) > 0.4:
        score -= 10
    elif away_style.get("defense") == "low_block" and home_style.get("attack", {}).get("through", 0) > 0.4:
        score += 10
    return max(0, min(100, score))
