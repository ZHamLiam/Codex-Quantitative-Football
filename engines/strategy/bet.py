from engines.strategy.risk import calc_expected_value, calc_risk_level

def kelly_criterion(sim_prob: float, odds: float, fraction: float = 0.25) -> float:
    b = odds - 1
    p = sim_prob / 100
    q = 1 - p
    raw_kelly = max(0, (b * p - q) / b) if b > 0 else 0
    return round(raw_kelly * fraction * 100, 2)

def generate_advice(sim_result: dict, odds_home: float = 2.0, odds_draw: float = 3.5, odds_away: float = 3.5) -> dict:
    outcomes = {
        "home": {"prob": sim_result["home_win_pct"], "odds": odds_home},
        "draw": {"prob": sim_result["draw_pct"], "odds": odds_draw},
        "away": {"prob": sim_result["away_win_pct"], "odds": odds_away},
    }

    best = None
    best_edge = -999
    for key, val in outcomes.items():
        ev = calc_expected_value(val["prob"], val["odds"])
        if ev > best_edge:
            best_edge = ev
            best = key

    risk = calc_risk_level(sim_result["variance"], best_edge)

    advice = {"expected_value": best_edge, "best_pick": best, "risk_level": risk, "suggestion": "avoid"}

    if best_edge > 0.05:
        advice["suggestion"] = "buy"
        advice["kelly_stake"] = kelly_criterion(outcomes[best]["prob"], outcomes[best]["odds"])
    elif best_edge > 0:
        advice["suggestion"] = "watch"

    return advice
