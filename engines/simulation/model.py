import numpy as np

def simulate_one_match(lambda_home: float, lambda_away: float, uncertainty: float = 0.0) -> tuple:
    var_factor = 1 + uncertainty * 3
    lam_h = max(0.05, np.random.normal(lambda_home, np.sqrt(lambda_home * var_factor)))
    lam_a = max(0.05, np.random.normal(lambda_away, np.sqrt(lambda_away * var_factor)))
    home_goals = np.random.poisson(lam_h)
    away_goals = np.random.poisson(lam_a)
    return home_goals, away_goals

def monte_carlo_simulate(lambda_home: float, lambda_away: float, uncertainty: float = 0.0, n: int = 10000) -> dict:
    results = {"home_wins": 0, "draws": 0, "away_wins": 0, "score_dist": {}, "total_goals": 0}

    for _ in range(n):
        h, a = simulate_one_match(lambda_home, lambda_away, uncertainty)
        results["total_goals"] += h + a
        key = f"{h}-{a}"
        results["score_dist"][key] = results["score_dist"].get(key, 0) + 1
        if h > a:
            results["home_wins"] += 1
        elif h == a:
            results["draws"] += 1
        else:
            results["away_wins"] += 1

    pct = {
        "home_win_pct": round(results["home_wins"] / n * 100, 2),
        "draw_pct": round(results["draws"] / n * 100, 2),
        "away_win_pct": round(results["away_wins"] / n * 100, 2),
        "expected_goals": round(results["total_goals"] / n, 2),
        "lambda_home": round(lambda_home, 4),
        "lambda_away": round(lambda_away, 4),
        "variance": round(1 + uncertainty * 3, 2),
        "simulations": n,
    }

    sorted_scores = sorted(results["score_dist"].items(), key=lambda x: x[1], reverse=True)[:5]
    pct["score_distribution"] = {k: round(v / n * 100, 2) for k, v in sorted_scores}

    return pct
