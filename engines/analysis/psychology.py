def calc_motivation(match_type: str, context: dict) -> float:
    base = 60
    if match_type == "derby":
        base += 20
    if context.get("is_knockout"):
        base += 25
    if context.get("can_win_league"):
        base += 20
    if context.get("relegation_battle"):
        base += 15
    return min(100, base)

def calc_morale(recent_results: list[str]) -> float:
    if not recent_results:
        return 50.0
    pts = {"W": 100, "D": 50, "L": 0}
    return sum(pts.get(r, 50) for r in recent_results[-5:]) / min(len(recent_results), 5)

def calc_experience(tournament_matches: int) -> float:
    if tournament_matches >= 20:
        return 100.0
    return tournament_matches * 5
